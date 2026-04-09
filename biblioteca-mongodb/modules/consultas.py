def consulta_copias(db):
    pipeline = [
        {"$lookup": {
            "from": "edicion",
            "localField": "isbn",
            "foreignField": "isbn",
            "as": "edicion"
        }},
        {"$unwind": "$edicion"},
        {"$lookup": {
            "from": "libro",
            "localField": "edicion.libro_titulo",
            "foreignField": "titulo",
            "as": "libro"
        }},
        {"$unwind": "$libro"},
        {"$lookup": {
            "from": "autorea",
            "localField": "edicion.libro_titulo",
            "foreignField": "libro_titulo",
            "as": "autores"
        }},
        {"$project": {
            "_id": 0,
            "numero": 1,
            "isbn": 1,
            "año": "$edicion.año",
            "idioma": "$edicion.idioma",
            "titulo": "$libro.titulo",
            "autores": "$autores.autor_nombre"
        }}
    ]
    return list(db.copia.aggregate(pipeline))


def consulta_libros_por_usuario(db, rut):
    pipeline = [
        {"$match": {"usuario_rut": rut}},
        {"$lookup": {
            "from": "edicion",
            "localField": "isbn_copia",
            "foreignField": "isbn",
            "as": "edicion"
        }},
        {"$unwind": "$edicion"},
        {"$project": {
            "_id": 0,
            "titulo": "$edicion.libro_titulo",
            "isbn_copia": 1,
            "numero_copia": 1,
            "fecha_prestamo": 1,
            "fecha_devolucion": 1
        }}
    ]
    return list(db.prestamo.aggregate(pipeline))
