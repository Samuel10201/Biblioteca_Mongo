from bson import ObjectId


def insertar_prestamo(db, isbn_copia, numero_copia, usuario_rut, fecha_prestamo, fecha_devolucion):
    db.prestamo.insert_one({
        "isbn_copia": isbn_copia,
        "numero_copia": numero_copia,
        "usuario_rut": usuario_rut,
        "fecha_prestamo": fecha_prestamo,
        "fecha_devolucion": fecha_devolucion
    })


def actualizar_prestamo(db, prestamo_id, datos):
    db.prestamo.update_one({"_id": ObjectId(prestamo_id)}, {"$set": datos})


def eliminar_prestamo(db, prestamo_id):
    db.prestamo.delete_one({"_id": ObjectId(prestamo_id)})


def obtener_prestamos(db, busqueda=""):
    filtro = {}
    if busqueda:
        filtro = {"usuario_rut": {"$regex": busqueda, "$options": "i"}}
    return list(db.prestamo.find(filtro))
