
from app_base.core.errors import ConflictError
from app_base.modules.cart.domain import Cart, CartLine, CartRepository
from app_base.modules.catalog.domain import ProductRepository


class CartService:
    def __init__(self, repository: CartRepository, products: ProductRepository):
        self.repository = repository
        self.products = products

    async def get(self, customer_id: str) -> Cart:
        return await self.repository.get_or_create(customer_id)

    async def add(self, customer_id: str, product_id: str, quantity: int) -> Cart:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        product = await self.products.get(product_id)
        if product is None or product.status.value != "published":
            raise ConflictError("product is not purchasable")
        cart = await self.get(customer_id)
        for line in cart.lines:
            if line.product_id == product_id:
                line.quantity += quantity
                await self.repository.save(cart)
                return cart
        cart.lines.append(CartLine(product.id, product.shop_id, quantity))
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
