def insertar_autor(db, nombre, libros):
    db.autor.insert_one({"nombre": nombre})

    for libro in libros:
        titulo = libro["titulo"]
        datos = libro.get("datos")

        if datos:
            db.libro.insert_one({"titulo": titulo})
            db.edicion.insert_one({
                "isbn": datos["isbn"],
                "año": datos["anio"],
                "idioma": datos["idioma"],
                "libro_titulo": titulo
            })
            db.copia.insert_one({
                "numero": datos["numero"],
                "isbn": datos["isbn"]
            })

        db.autorea.insert_one({"autor_nombre": nombre, "libro_titulo": titulo})



def actualizar_autor(db, nombre_actual, nombre_nuevo):
    db.autor.update_one({"nombre": nombre_actual}, {"$set": {"nombre": nombre_nuevo}})
    db.autorea.update_many({"autor_nombre": nombre_actual}, {"$set": {"autor_nombre": nombre_nuevo}})


def eliminar_autor(db, nombre):
    parejas = list(db.autorea.find({"autor_nombre": nombre}))
    db.autorea.delete_many({"autor_nombre": nombre})

    for pareja in parejas:
        titulo = pareja["libro_titulo"]
        if db.autorea.count_documents({"libro_titulo": titulo}) == 0:
            eliminar_libro(db, titulo)

    db.autor.delete_one({"nombre": nombre})


def obtener_autores(db, busqueda=""):
    """
        input: busqueda es el filtro, en este caso el nombre del autor.
        output: lista de resultados del filtro.

        filtro es lo que se le pasa a la funcion de pymongo .find(), que como
        argumento recibe un diccionario con los atributos a buscar. El condicional
        es para verficar que no este vacio, si lo esta, se retorna toda la coleccion
        sin filtro. 

        "$regex" define la secuencia de palabras a buscar, el nombre, y "$options":"i"
        hace que se acepten busquedas que cumplan la secuencia de letras definida en 
        regex sin importar mayusculas y minusculas. La "i" viene de "insensitive".
    """
    filtro = {}
    if busqueda:
        filtro = {"nombre": {"$regex": busqueda, "$options": "i"}}
    return list(db.autor.find(filtro))


def insertar_libro(db, titulo, autores_nombres, isbn, anio, idioma, numero, nuevos_autores=None):
    db.libro.insert_one({"titulo": titulo})

    if nuevos_autores:
        for nombre in nuevos_autores:
            db.autor.insert_one({"nombre": nombre})

    for nombre in autores_nombres:
        db.autorea.insert_one({"autor_nombre": nombre, "libro_titulo": titulo})

    db.edicion.insert_one({"isbn": isbn, "año": anio, "idioma": idioma, "libro_titulo": titulo})
    db.copia.insert_one({"numero": numero, "isbn": isbn})


def actualizar_libro(db, titulo_actual, titulo_nuevo):
    db.libro.update_one({"titulo": titulo_actual}, {"$set": {"titulo": titulo_nuevo}})
    db.autorea.update_many({"libro_titulo": titulo_actual}, {"$set": {"libro_titulo": titulo_nuevo}})
    db.edicion.update_many({"libro_titulo": titulo_actual}, {"$set": {"libro_titulo": titulo_nuevo}})


def eliminar_libro(db, titulo):
    parejas = list(db.autorea.find({"libro_titulo": titulo}))
    db.autorea.delete_many({"libro_titulo": titulo})

    for pareja in parejas:
        autor_nombre = pareja["autor_nombre"]
        if db.autorea.count_documents({"autor_nombre": autor_nombre}) == 0:
            db.autor.delete_one({"nombre": autor_nombre})

    ediciones = list(db.edicion.find({"libro_titulo": titulo}))
    for edicion in ediciones:
        db.copia.delete_many({"isbn": edicion["isbn"]})
    db.edicion.delete_many({"libro_titulo": titulo})

    db.libro.delete_one({"titulo": titulo})


def obtener_libros(db, busqueda=""):
    filtro = {}
    if busqueda:
        filtro = {"titulo": {"$regex": busqueda, "$options": "i"}}
    return list(db.libro.find(filtro))


def insertar_edicion(db, isbn, anio, idioma, libro_titulo, numero):
    db.edicion.insert_one({"isbn": isbn, "año": anio, "idioma": idioma, "libro_titulo": libro_titulo})
    db.copia.insert_one({"numero": numero, "isbn": isbn})


def actualizar_edicion(db, isbn_actual, datos):
    db.edicion.update_one({"isbn": isbn_actual}, {"$set": datos})

    if "isbn" in datos and datos["isbn"] != isbn_actual:
        db.copia.update_many({"isbn": isbn_actual}, {"$set": {"isbn": datos["isbn"]}})
        db.prestamo.update_many({"isbn_copia": isbn_actual}, {"$set": {"isbn_copia": datos["isbn"]}})


def eliminar_edicion(db, isbn):
    edicion = db.edicion.find_one({"isbn": isbn})
    if not edicion:
        return

    libro_titulo = edicion["libro_titulo"]

    db.copia.delete_many({"isbn": isbn})
    db.edicion.delete_one({"isbn": isbn})

    if db.edicion.count_documents({"libro_titulo": libro_titulo}) == 0:
        eliminar_libro(db, libro_titulo)


def obtener_ediciones(db, busqueda=""):
    filtro = {}
    if busqueda:
        filtro = {"isbn": {"$regex": busqueda, "$options": "i"}}
    return list(db.edicion.find(filtro))


def insertar_copia(db, numero, isbn):
    db.copia.insert_one({"numero": numero, "isbn": isbn})


def actualizar_copia(db, numero_actual, isbn, numero_nuevo):
    db.copia.update_one({"numero": numero_actual, "isbn": isbn}, {"$set": {"numero": numero_nuevo}})
    db.prestamo.update_many(
        {"numero_copia": numero_actual, "isbn_copia": isbn},
        {"$set": {"numero_copia": numero_nuevo}}
    )


def eliminar_copia(db, numero, isbn):
    db.copia.delete_one({"numero": numero, "isbn": isbn})


def obtener_copias(db, busqueda=""):
    filtro = {}
    if busqueda:
        filtro = {"isbn": {"$regex": busqueda, "$options": "i"}}
    return list(db.copia.find(filtro))
