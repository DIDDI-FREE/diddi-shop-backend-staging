
from app_base.core.errors import ConflictError, InsufficientStockError
from app_base.modules.cart.domain import Cart, CartLine, CartRepository
from app_base.modules.catalog.domain import ProductRepository


class CartService:
    def __init__(self, repository: CartRepository, products: ProductRepository):
        self.repository = repository
        self.products = products

    async def get(self, customer_id: str) -> Cart:
        return await self.repository.get_or_create(customer_id)

    async def details(self, customer_id: str) -> tuple[Cart, list[dict], list[dict]]:
        cart = await self.get(customer_id)
        lines: list[dict] = []
        shop_totals: dict[str, int] = {}
        for line in cart.lines:
            product = await self.products.get(line.product_id)
            if product is None:
                continue
            line_total = product.price_minor * line.quantity
            lines.append({
                "product_id": line.product_id,
                "shop_id": line.shop_id,
                "quantity": line.quantity,
                "title": product.title,
                "unit_price_minor": product.price_minor,
                "line_total_minor": line_total,
            })
            shop_totals[line.shop_id] = shop_totals.get(line.shop_id, 0) + line_total
        shops = [
            {"shop_id": shop_id, "subtotal_minor": subtotal_minor}
            for shop_id, subtotal_minor in sorted(shop_totals.items())
        ]
        return cart, lines, shops

    async def add(self, customer_id: str, product_id: str, quantity: int) -> Cart:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        product = await self.products.get(product_id)
        if product is None or product.status.value != "published":
            raise ConflictError("product is not purchasable")
        cart = await self.get(customer_id)
        for line in cart.lines:
            if line.product_id == product_id:
                if product.stock < line.quantity + quantity:
                    raise InsufficientStockError(
                        "Stock insuffisant",
                        details={
                            "product_id": product_id,
                            "requested_quantity": line.quantity + quantity,
                            "available_quantity": product.stock,
                        },
                    )
                line.quantity += quantity
                await self.repository.save(cart)
                return cart
        if product.stock < quantity:
            raise InsufficientStockError(
                "Stock insuffisant",
                details={
                    "product_id": product_id,
                    "requested_quantity": quantity,
                    "available_quantity": product.stock,
                },
            )
        cart.lines.append(CartLine(product.id, product.shop_id, quantity))
        await self.repository.save(cart)
        return cart

    async def set_quantity(self, customer_id: str, product_id: str, quantity: int) -> Cart:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        cart = await self.get(customer_id)
        line = next((line for line in cart.lines if line.product_id == product_id), None)
        if line is None:
            raise ConflictError("cart line not found")
        product = await self.products.get(product_id)
        if product is None or product.status.value != "published":
            raise ConflictError("product is not purchasable")
        if product.stock < quantity:
            raise InsufficientStockError(
                "Stock insuffisant",
                details={
                    "product_id": product_id,
                    "requested_quantity": quantity,
                    "available_quantity": product.stock,
                },
            )
        line.quantity = quantity
        await self.repository.save(cart)
        return cart

    async def remove(self, customer_id: str, product_id: str) -> Cart:
        cart = await self.get(customer_id)
        original_size = len(cart.lines)
        cart.lines = [line for line in cart.lines if line.product_id != product_id]
        if len(cart.lines) == original_size:
            raise ConflictError("cart line not found")
        await self.repository.save(cart)
        return cart
