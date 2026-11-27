from datetime import UTC, datetime, timedelta

from app_base.core.errors import ConflictError
from app_base.modules.delivery.domain import DeliveryProjection, DeliveryStatus
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus
from app_base.shared_kernel.contracts.delivery import DeliveryCommand


class DeliveryService:
    def __init__(self, repository, sender, orders: OrderService, seller_release_enabled: bool = False):
        self.repository = repository
        self.sender = sender
        self.orders = orders
        self.seller_release_enabled = seller_release_enabled

    async def request_for_order(self, order_id: str) -> DeliveryProjection:
        existing = await self.repository.get_by_order(order_id)
        if existing is not None:
            return existing
        order = await self.orders.get(order_id)
        if order.fulfillment_status != FulfillmentStatus.READY_FOR_PICKUP:
            raise ConflictError("order is not ready for pickup")
        payload = dict(order.metadata.get("delivery_request", {}))
        payload.setdefault("order_reference", f"shop-order:{order.id}")
        payload.setdefault("customer_user_id", payload.get("customer_user_id", "unknown"))
        response = await self.sender.create_delivery(
            DeliveryCommand(order_id=order.id, idempotency_key=f"shop:create-delivery:{order.id}:1"),
            payload,
        )
        delivery = response.get("delivery", response)
        projection = DeliveryProjection(delivery["id"], order.id, DeliveryStatus.REQUESTED)
        await self.repository.save(projection)
        order.delivery_id = projection.id
        await self.orders.repository.save(order)
        return projection

    async def mark_ready_and_request(self, order_id: str) -> DeliveryProjection:
        """Mark a seller-ready order and immediately create its DiddiSend delivery.

        Repeating the command after a timeout is safe: an existing projection is
        returned and ``request_for_order`` does not create a second delivery.
        """
        order = await self.orders.get(order_id)
        if order.fulfillment_status == FulfillmentStatus.TO_PREPARE:
            await self.orders.transition(
                order_id,
                FulfillmentStatus.READY_FOR_PICKUP,
                reason="seller_ready",
                actor="seller",
            )
        elif order.fulfillment_status != FulfillmentStatus.READY_FOR_PICKUP:
            raise ConflictError("order is not being prepared")
        return await self.request_for_order(order_id)

    async def apply_event(self, order_id: str, event_type: str, payload: dict) -> DeliveryProjection:
        target = {
            "delivery.created": DeliveryStatus.REQUESTED,
            "delivery.assigned": DeliveryStatus.ASSIGNED,
            "delivery.picked_up": DeliveryStatus.PICKED_UP,
            "delivery.in_transit": DeliveryStatus.IN_TRANSIT,
            "delivery.delivered": DeliveryStatus.DELIVERED,
            "delivery.failed": DeliveryStatus.FAILED,
            "delivery.returned": DeliveryStatus.RETURNED,
        }.get(event_type)
        if target is None:
            raise ConflictError(f"unsupported delivery event {event_type}")
        current = await self.repository.get_by_order(order_id)
        delivery = current or DeliveryProjection(payload.get("delivery_id", "unknown"), order_id, target)
        delivery.status = target
        delivery.proof_ref = payload.get("proof_ref") or payload.get("proof_id")
        delivery.tracking = payload.get("tracking")
        courier = payload.get("courier") or payload.get("courier_info")
        if courier:
            delivery.courier = {
                "id": courier.get("id") or courier.get("courier_id"),
                "name": courier.get("name") or courier.get("display_name"),
                "phone_masked": courier.get("phone_masked") or courier.get("masked_phone"),
                "avatar_url": courier.get("avatar_url"),
                "vehicle_type": courier.get("vehicle_type") or courier.get("vehicle"),
            }
        delivery.dropoff_code = payload.get("dropoff_code") or payload.get("delivery_code")
        position = payload.get("position") or payload.get("courier_position")
        latitude = position.get("latitude", position.get("lat")) if position else None
        longitude = position.get("longitude", position.get("lng")) if position else None
        if latitude is not None and longitude is not None:
            delivery.position = {
                "latitude": latitude,
                "longitude": longitude,
                "updated_at": position.get("updated_at") or position.get("recorded_at"),
            }
        await self.repository.save(delivery)
        order = await self.orders.get(order_id)
        transition = {
            DeliveryStatus.PICKED_UP: FulfillmentStatus.PICKED_UP,
            DeliveryStatus.IN_TRANSIT: FulfillmentStatus.IN_TRANSIT,
            DeliveryStatus.DELIVERED: FulfillmentStatus.DELIVERED,
            DeliveryStatus.FAILED: FulfillmentStatus.FAILED,
            DeliveryStatus.RETURNED: FulfillmentStatus.RETURNED,
        }.get(target)
        if transition and order.fulfillment_status != transition:
            order = await self.orders.transition(order_id, transition, reason=event_type, actor="diddisend")
        if target == DeliveryStatus.DELIVERED:
            now = datetime.now(UTC)
            order.metadata.setdefault("delivered_at", now)
            if self.seller_release_enabled:
                order.metadata.setdefault("release_eligible_at", now + timedelta(hours=72))
            await self.orders.repository.save(order)
        return delivery
