from pydantic import BaseModel
from sqlmodel import Session, select
from db.modelos import Pedidos, ProductosEnPedidos, Productos
from db.conexcion import db

class ProductosEnPedidoRegistrar(BaseModel):
    producto_id: str
    cantidad: int

class PedidoARegistrar(BaseModel):
    cliente_id: str
    productos: list[ProductosEnPedidoRegistrar]

def registrar(pedidoARegistrar: PedidoARegistrar):
    with Session(db) as sesion:
        # Obtener IDs de los productos del pedido
        productos_ids = [producto.producto_id for producto in pedidoARegistrar.productos]

        # Verificar si los productos existen en la base de datos
        productos_existentes = sesion.exec(
            select(Productos.id).where(Productos.id.in_(productos_ids))
        ).all()

        # Convertir los resultados en un conjunto para comparación
        productos_existentes_set = set(productos_existentes)
        productos_solicitados_set = set(productos_ids)

        # Si falta algún producto, devolver error
        productos_no_encontrados = productos_solicitados_set - productos_existentes_set
        if productos_no_encontrados:
            return {
                "error": "Algunos productos no existen.",
                "productos_no_encontrados": list(productos_no_encontrados),
            }

        # Crear el pedido
        pedido = Pedidos(cliente_id=pedidoARegistrar.cliente_id)
        sesion.add(pedido)
        sesion.commit()  # Se confirma para generar el ID del pedido
        sesion.refresh(pedido)

        # Agregar productos al pedido
        for producto in pedidoARegistrar.productos:
            sesion.add(
                ProductosEnPedidos(
                    pedido_id=pedido.id,
                    producto_id=producto.producto_id,
                    cantidad=producto.cantidad
                )
            )

        sesion.commit()
        sesion.refresh(pedido)
        return pedido