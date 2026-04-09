def insertar_usuario(db, rut, nombre):
    db.usuario.insert_one({"rut": rut, "nombre": nombre})


def actualizar_usuario(db, rut, nombre_nuevo):
    db.usuario.update_one({"rut": rut}, {"$set": {"nombre": nombre_nuevo}})


def eliminar_usuario(db, rut):
    db.usuario.delete_one({"rut": rut})


def obtener_usuarios(db, busqueda=""):
    filtro = {}
    if busqueda:
        filtro = {"rut": {"$regex": busqueda, "$options": "i"}}
    return list(db.usuario.find(filtro))
