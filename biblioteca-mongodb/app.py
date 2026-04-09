from flask import Flask, render_template, request, redirect, url_for
from bson import ObjectId
from modules.db import get_database
from modules import autor_libro, usuario, prestamo, consultas

app = Flask(__name__)
db = get_database()


@app.route("/")
def inicio():
    return render_template("inicio.html")


# --- RUTAS AUTOR ---

"""
    Esta funcion cumple dos tareas, la de mostrar los datos de
    la coleccion autores por completo, y la de mostrar el resultado
    de la busqueda de un autor. 
    La forma en la que funciona es la siguiente, o bueno, esta es 
    la secuencia con la que trabaja:
    1. El usuario elige 'autores' en el menu.
    2. Al elegir autores se ejecuta esta funcion, y el valor
    que toma 'busqueda' es vacio, entonces se hara una busqueda
    en la coleccion sin filtro, mostrando todos los datos de la
    coleccion.
    De esta forma funciona para mostrar toda la coleccion. Ahora
    como muestra la busqueda filtrada.
    1. El usuario rellena el formulario para la busqueda y 
    presiona el boton para mandar la busqueda.
    2. El formulario usa GET, entonces los datos del formulario
    seran visibles en la URL, y de esta forma se guarda el filtro.
    3. Con action="/actores" se reenvia a /autores para que 
    se ejecute la funcion listar_autores(), pero esta vez
    si se encontraran datos en la URL al usar 
    request.args.get("busqueda"), siendo 'busqueda' en name que
    se le pone al input.
"""
@app.route("/autores")
def listar_autores():
    #Busca en la URL el valor de 'busqueda', name puesto 
    #al input en 'autores.html'.
    busqueda = request.args.get("busqueda", "")
    autores = autor_libro.obtener_autores(db, busqueda)
    return render_template("autores.html", autores=autores, busqueda=busqueda, seccion="catalogo", sub="autores")


@app.route("/autores/crear", methods=["GET", "POST"])
def crear_autor():
    if request.method == "POST":
        """
            Aca se usa .get() pq inicialmente el formulario no da este
            valor, entonces si se usa directamente .form[] se rompe la
            pagina, pero con get() solo retorna None.

            "crear_libro" existe SOLO cuando se cumple la condicion
            de que "libro_no_existe=True", y toma el valor de "1"
            cuando se cumple que "libro_no_existe=1" entonces solo
            toma valor de 1 cuando el libro_no_existe, mientras no se
            asuma que existe, se hara la comparacio None=="1" que 
            siempre dara False, definiendo que no hay necesidad de crear
            un libro nuevo.
        """
        nombre = request.form["nombre"]
        titulos_texto = request.form["titulos"]
        titulos = [t.strip() for t in titulos_texto.split(",") if t.strip()]
        crear_libros = request.form.get("crear_libros") == "1"

        """
            Verifica si el autor ya existe, de ser asi, salta un error
            diciendo que este autor ya existe en la coleccion. Si el 
            autor no existe, entonces se revisa si el libro al que 
            esta asociado existe.
        """
        if db.autor.find_one({"nombre": nombre}):
            autores = autor_libro.obtener_autores(db)
            return render_template("insertar_autor.html", operacion="crear", autores=autores,
                seccion="catalogo", sub="autores",
                error="Error: Este nombre ya existe en esta colección",
                nombre=nombre, titulos_texto=titulos_texto)

        libros_faltantes = [t for t in titulos if not db.libro.find_one({"titulo": t})]

        """
            Si el libro no existe actualmente, y aun no se ha mostrado
            el menu para crear el libro, entonces se declara que 
            libro_no_existe=True, para que se muestre el menu de 
            creacion del libro.
        """
        if libros_faltantes and not crear_libros:
            autores = autor_libro.obtener_autores(db)
            return render_template("insertar_autor.html", operacion="crear", autores=autores,
                seccion="catalogo", sub="autores",
                libros_faltantes=libros_faltantes, nombre=nombre, titulos_texto=titulos_texto)

        """
            Aplica despues de que se haya mostrado el menu para crear
            el libro.
        """
        libros = []
        if crear_libros:
            num_faltantes = int(request.form["num_faltantes"])
            datos_faltantes = {}
            for i in range(num_faltantes):
                titulo_f = request.form[f"titulo_faltante_{i}"]
                datos_faltantes[titulo_f] = {
                    "isbn": request.form[f"isbn_{i}"],
                    "anio": int(request.form[f"anio_{i}"]),
                    "idioma": request.form[f"idioma_{i}"],
                    "numero": int(request.form[f"numero_{i}"])
                }
            for titulo in titulos:
                if titulo in datos_faltantes:
                    libros.append({"titulo": titulo, "datos": datos_faltantes[titulo]})
                else:
                    libros.append({"titulo": titulo})
        else:
            for titulo in titulos:
                libros.append({"titulo": titulo})

        autor_libro.insertar_autor(db, nombre, libros)
        return redirect("/autores")

    autores = autor_libro.obtener_autores(db)
    return render_template("insertar_autor.html", operacion="crear", autores=autores,
        seccion="catalogo", sub="autores")


@app.route("/autores/editar", methods=["GET", "POST"])
def editar_autor():
    if request.method == "POST":
        nombre_actual = request.form["nombre_actual"]
        nombre_nuevo = request.form["nombre_nuevo"]

        if not db.autor.find_one({"nombre": nombre_actual}):
            autores = autor_libro.obtener_autores(db)
            return render_template("editar_autor.html", operacion="editar", autores=autores,
                seccion="catalogo", sub="autores",
                error="Error: No se encontró un autor con ese nombre",
                nombre_actual=nombre_actual, nombre_nuevo=nombre_nuevo)

        if nombre_actual != nombre_nuevo and db.autor.find_one({"nombre": nombre_nuevo}):
            autores = autor_libro.obtener_autores(db)
            return render_template("editar_autor.html", operacion="editar", autores=autores,
                seccion="catalogo", sub="autores",
                error="Error: Este nombre ya existe en esta colección",
                nombre_actual=nombre_actual, nombre_nuevo=nombre_nuevo)

        autor_libro.actualizar_autor(db, nombre_actual, nombre_nuevo)
        return redirect("/autores")

    autores = autor_libro.obtener_autores(db)
    return render_template("editar_autor.html", operacion="editar", autores=autores,
        seccion="catalogo", sub="autores")


@app.route("/autores/eliminar", methods=["GET", "POST"])
def eliminar_autor_ruta():
    if request.method == "POST":
        nombre = request.form["nombre"]

        if not db.autor.find_one({"nombre": nombre}):
            autores = autor_libro.obtener_autores(db)
            return render_template("eliminar_autor.html", operacion="eliminar", autores=autores,
                seccion="catalogo", sub="autores",
                error="Error: No se encontró un autor con ese nombre",
                nombre=nombre)

        autor_libro.eliminar_autor(db, nombre)
        return redirect("/autores")

    autores = autor_libro.obtener_autores(db)
    return render_template("eliminar_autor.html", operacion="eliminar", autores=autores,
        seccion="catalogo", sub="autores")


# --- RUTAS LIBRO ---

@app.route("/libros")
def listar_libros():
    busqueda = request.args.get("busqueda", "")
    libros = autor_libro.obtener_libros(db, busqueda)
    return render_template("libros.html", libros=libros, busqueda=busqueda, seccion="catalogo", sub="libros")


@app.route("/libros/crear", methods=["GET", "POST"])
def crear_libro():
    if request.method == "POST":
        titulo = request.form["titulo"]
        autores_texto = request.form["autores"]
        autores_nombres = [a.strip() for a in autores_texto.split(",") if a.strip()]
        crear_autores = request.form.get("crear_autores") == "1"

        if db.libro.find_one({"titulo": titulo}):
            libros = autor_libro.obtener_libros(db)
            return render_template("insertar_libro.html", operacion="crear", libros=libros,
                seccion="catalogo", sub="libros",
                error="Error: Este título ya existe en esta colección",
                titulo=titulo, autores_texto=autores_texto,
                isbn=request.form.get("isbn", ""), anio=request.form.get("anio", ""),
                idioma=request.form.get("idioma", ""), numero=request.form.get("numero", ""))

        autores_faltantes = [a for a in autores_nombres if not db.autor.find_one({"nombre": a})]

        if autores_faltantes and not crear_autores:
            libros = autor_libro.obtener_libros(db)
            return render_template("insertar_libro.html", operacion="crear", libros=libros,
                seccion="catalogo", sub="libros",
                autores_faltantes=autores_faltantes, titulo=titulo, autores_texto=autores_texto,
                isbn=request.form.get("isbn", ""), anio=request.form.get("anio", ""),
                idioma=request.form.get("idioma", ""), numero=request.form.get("numero", ""))

        isbn = request.form["isbn"]
        anio = int(request.form["anio"])
        idioma = request.form["idioma"]
        numero = int(request.form["numero"])

        nuevos_autores = autores_faltantes if crear_autores else None
        autor_libro.insertar_libro(db, titulo, autores_nombres, isbn, anio, idioma, numero, nuevos_autores)
        return redirect("/libros")

    libros = autor_libro.obtener_libros(db)
    return render_template("insertar_libro.html", operacion="crear", libros=libros,
        seccion="catalogo", sub="libros")


@app.route("/libros/editar", methods=["GET", "POST"])
def editar_libro():
    if request.method == "POST":
        titulo_actual = request.form["titulo_actual"]
        titulo_nuevo = request.form["titulo_nuevo"]

        if not db.libro.find_one({"titulo": titulo_actual}):
            libros = autor_libro.obtener_libros(db)
            return render_template("editar_libro.html", operacion="editar", libros=libros,
                seccion="catalogo", sub="libros",
                error="Error: No se encontró un libro con ese título",
                titulo_actual=titulo_actual, titulo_nuevo=titulo_nuevo)

        if titulo_actual != titulo_nuevo and db.libro.find_one({"titulo": titulo_nuevo}):
            libros = autor_libro.obtener_libros(db)
            return render_template("editar_libro.html", operacion="editar", libros=libros,
                seccion="catalogo", sub="libros",
                error="Error: Este título ya existe en esta colección",
                titulo_actual=titulo_actual, titulo_nuevo=titulo_nuevo)

        autor_libro.actualizar_libro(db, titulo_actual, titulo_nuevo)
        return redirect("/libros")

    libros = autor_libro.obtener_libros(db)
    return render_template("editar_libro.html", operacion="editar", libros=libros,
        seccion="catalogo", sub="libros")


@app.route("/libros/eliminar", methods=["GET", "POST"])
def eliminar_libro_ruta():
    if request.method == "POST":
        titulo = request.form["titulo"]

        if not db.libro.find_one({"titulo": titulo}):
            libros = autor_libro.obtener_libros(db)
            return render_template("eliminar_libro.html", operacion="eliminar", libros=libros,
                seccion="catalogo", sub="libros",
                error="Error: No se encontró un libro con ese título",
                titulo=titulo)

        autor_libro.eliminar_libro(db, titulo)
        return redirect("/libros")

    libros = autor_libro.obtener_libros(db)
    return render_template("eliminar_libro.html", operacion="eliminar", libros=libros,
        seccion="catalogo", sub="libros")


# --- RUTAS EDICION ---

@app.route("/ediciones")
def listar_ediciones():
    busqueda = request.args.get("busqueda", "")
    ediciones = autor_libro.obtener_ediciones(db, busqueda)
    return render_template("ediciones.html", ediciones=ediciones, busqueda=busqueda, seccion="catalogo", sub="ediciones")


@app.route("/ediciones/crear", methods=["GET", "POST"])
def crear_edicion():
    if request.method == "POST":
        libro_titulo = request.form["libro_titulo"]
        isbn = request.form["isbn"]
        anio = int(request.form["anio"])
        idioma = request.form["idioma"]
        numero = int(request.form["numero"])

        if not db.libro.find_one({"titulo": libro_titulo}):
            ediciones = autor_libro.obtener_ediciones(db)
            return render_template("insertar_edicion.html", operacion="crear", ediciones=ediciones,
                seccion="catalogo", sub="ediciones",
                error="Error: No se encontró un libro con ese título. Créelo primero.",
                libro_titulo=libro_titulo, isbn=isbn, anio=anio, idioma=idioma, numero=numero)

        if db.edicion.find_one({"isbn": isbn}):
            ediciones = autor_libro.obtener_ediciones(db)
            return render_template("insertar_edicion.html", operacion="crear", ediciones=ediciones,
                seccion="catalogo", sub="ediciones",
                error="Error: Este ISBN ya existe en esta colección",
                libro_titulo=libro_titulo, isbn=isbn, anio=anio, idioma=idioma, numero=numero)

        autor_libro.insertar_edicion(db, isbn, anio, idioma, libro_titulo, numero)
        return redirect("/ediciones")

    ediciones = autor_libro.obtener_ediciones(db)
    return render_template("insertar_edicion.html", operacion="crear", ediciones=ediciones,
        seccion="catalogo", sub="ediciones")


@app.route("/ediciones/editar", methods=["GET", "POST"])
def editar_edicion():
    if request.method == "POST":
        isbn_actual = request.form["isbn_actual"]
        isbn_nuevo = request.form["isbn"]
        anio = int(request.form["anio"])
        idioma = request.form["idioma"]

        if not db.edicion.find_one({"isbn": isbn_actual}):
            ediciones = autor_libro.obtener_ediciones(db)
            return render_template("editar_edicion.html", operacion="editar", ediciones=ediciones,
                seccion="catalogo", sub="ediciones",
                error="Error: No se encontró una edición con ese ISBN",
                isbn_actual=isbn_actual)

        if isbn_actual != isbn_nuevo and db.edicion.find_one({"isbn": isbn_nuevo}):
            edicion = db.edicion.find_one({"isbn": isbn_actual})
            ediciones = autor_libro.obtener_ediciones(db)
            return render_template("editar_edicion.html", operacion="editar", ediciones=ediciones,
                seccion="catalogo", sub="ediciones", edicion=edicion,
                error="Error: Este ISBN ya existe en esta colección",
                isbn_actual=isbn_actual)

        datos = {"isbn": isbn_nuevo, "año": anio, "idioma": idioma}
        autor_libro.actualizar_edicion(db, isbn_actual, datos)
        return redirect("/ediciones")

    isbn_actual = request.args.get("isbn_actual", "")
    edicion = None
    error = None
    if isbn_actual:
        edicion = db.edicion.find_one({"isbn": isbn_actual})
        if not edicion:
            error = "Error: No se encontró una edición con ese ISBN"

    ediciones = autor_libro.obtener_ediciones(db)
    return render_template("editar_edicion.html", operacion="editar", ediciones=ediciones,
        seccion="catalogo", sub="ediciones", edicion=edicion,
        isbn_actual=isbn_actual, error=error)


@app.route("/ediciones/eliminar", methods=["GET", "POST"])
def eliminar_edicion_ruta():
    if request.method == "POST":
        isbn = request.form["isbn"]

        if not db.edicion.find_one({"isbn": isbn}):
            ediciones = autor_libro.obtener_ediciones(db)
            return render_template("eliminar_edicion.html", operacion="eliminar", ediciones=ediciones,
                seccion="catalogo", sub="ediciones",
                error="Error: No se encontró una edición con ese ISBN",
                isbn=isbn)

        autor_libro.eliminar_edicion(db, isbn)
        return redirect("/ediciones")

    ediciones = autor_libro.obtener_ediciones(db)
    return render_template("eliminar_edicion.html", operacion="eliminar", ediciones=ediciones,
        seccion="catalogo", sub="ediciones")


# --- RUTAS COPIA ---

@app.route("/copias")
def listar_copias():
    busqueda = request.args.get("busqueda", "")
    copias = autor_libro.obtener_copias(db, busqueda)
    return render_template("copias.html", copias=copias, busqueda=busqueda, seccion="catalogo", sub="copias")


@app.route("/copias/crear", methods=["GET", "POST"])
def crear_copia():
    if request.method == "POST":
        isbn = request.form["isbn"]
        numero = int(request.form["numero"])

        if not db.edicion.find_one({"isbn": isbn}):
            copias = autor_libro.obtener_copias(db)
            return render_template("insertar_copia.html", operacion="crear", copias=copias,
                seccion="catalogo", sub="copias",
                error="Error: No se encontró una edición con ese ISBN. Créela primero.",
                isbn=isbn, numero=numero)

        if db.copia.find_one({"numero": numero, "isbn": isbn}):
            copias = autor_libro.obtener_copias(db)
            return render_template("insertar_copia.html", operacion="crear", copias=copias,
                seccion="catalogo", sub="copias",
                error="Error: Esta copia ya existe en esta colección",
                isbn=isbn, numero=numero)

        autor_libro.insertar_copia(db, numero, isbn)
        return redirect("/copias")

    copias = autor_libro.obtener_copias(db)
    return render_template("insertar_copia.html", operacion="crear", copias=copias,
        seccion="catalogo", sub="copias")


@app.route("/copias/editar", methods=["GET", "POST"])
def editar_copia():
    if request.method == "POST":
        isbn = request.form["isbn"]
        numero_actual = int(request.form["numero_actual"])
        numero_nuevo = int(request.form["numero_nuevo"])

        if not db.copia.find_one({"numero": numero_actual, "isbn": isbn}):
            copias = autor_libro.obtener_copias(db)
            return render_template("editar_copia.html", operacion="editar", copias=copias,
                seccion="catalogo", sub="copias",
                error="Error: No se encontró esa copia",
                isbn=isbn, numero_actual=numero_actual)

        if numero_actual != numero_nuevo and db.copia.find_one({"numero": numero_nuevo, "isbn": isbn}):
            copia = db.copia.find_one({"numero": numero_actual, "isbn": isbn})
            copias = autor_libro.obtener_copias(db)
            return render_template("editar_copia.html", operacion="editar", copias=copias,
                seccion="catalogo", sub="copias", copia=copia,
                error="Error: Esta copia ya existe en esta colección",
                isbn=isbn, numero_actual=numero_actual)

        autor_libro.actualizar_copia(db, numero_actual, isbn, numero_nuevo)
        return redirect("/copias")

    isbn = request.args.get("isbn", "")
    numero_actual = request.args.get("numero_actual", "")
    copia = None
    error = None
    if isbn and numero_actual:
        copia = db.copia.find_one({"isbn": isbn, "numero": int(numero_actual)})
        if not copia:
            error = "Error: No se encontró esa copia"

    copias = autor_libro.obtener_copias(db)
    return render_template("editar_copia.html", operacion="editar", copias=copias,
        seccion="catalogo", sub="copias", copia=copia,
        isbn=isbn, numero_actual=numero_actual, error=error)


@app.route("/copias/eliminar", methods=["GET", "POST"])
def eliminar_copia_ruta():
    if request.method == "POST":
        isbn = request.form["isbn"]
        numero = int(request.form["numero"])

        if not db.copia.find_one({"numero": numero, "isbn": isbn}):
            copias = autor_libro.obtener_copias(db)
            return render_template("eliminar_copia.html", operacion="eliminar", copias=copias,
                seccion="catalogo", sub="copias",
                error="Error: No se encontró esa copia",
                isbn=isbn, numero=numero)

        autor_libro.eliminar_copia(db, numero, isbn)
        return redirect("/copias")

    copias = autor_libro.obtener_copias(db)
    return render_template("eliminar_copia.html", operacion="eliminar", copias=copias,
        seccion="catalogo", sub="copias")


# --- RUTAS USUARIO ---

@app.route("/usuarios")
def listar_usuarios():
    busqueda = request.args.get("busqueda", "")
    usuarios = usuario.obtener_usuarios(db, busqueda)
    return render_template("usuarios.html", usuarios=usuarios, busqueda=busqueda, seccion="usuarios")


@app.route("/usuarios/crear", methods=["GET", "POST"])
def crear_usuario():
    if request.method == "POST":
        rut = request.form["rut"]
        nombre = request.form["nombre"]

        if db.usuario.find_one({"rut": rut}):
            usuarios = usuario.obtener_usuarios(db)
            return render_template("insertar_usuario.html", operacion="crear", usuarios=usuarios,
                seccion="usuarios",
                error="Error: Este RUT ya existe en esta colección",
                rut=rut, nombre=nombre)

        usuario.insertar_usuario(db, rut, nombre)
        return redirect("/usuarios")

    usuarios = usuario.obtener_usuarios(db)
    return render_template("insertar_usuario.html", operacion="crear", usuarios=usuarios,
        seccion="usuarios")


@app.route("/usuarios/editar", methods=["GET", "POST"])
def editar_usuario():
    if request.method == "POST":
        rut = request.form["rut"]
        nombre_nuevo = request.form["nombre_nuevo"]

        if not db.usuario.find_one({"rut": rut}):
            usuarios = usuario.obtener_usuarios(db)
            return render_template("editar_usuario.html", operacion="editar", usuarios=usuarios,
                seccion="usuarios",
                error="Error: No se encontró un usuario con ese RUT",
                rut=rut)

        usuario.actualizar_usuario(db, rut, nombre_nuevo)
        return redirect("/usuarios")

    rut = request.args.get("rut", "")
    usr = None
    error = None
    if rut:
        usr = db.usuario.find_one({"rut": rut})
        if not usr:
            error = "Error: No se encontró un usuario con ese RUT"

    usuarios = usuario.obtener_usuarios(db)
    return render_template("editar_usuario.html", operacion="editar", usuarios=usuarios,
        seccion="usuarios", usuario=usr, rut=rut, error=error)


@app.route("/usuarios/eliminar", methods=["GET", "POST"])
def eliminar_usuario_ruta():
    if request.method == "POST":
        rut = request.form["rut"]

        if not db.usuario.find_one({"rut": rut}):
            usuarios = usuario.obtener_usuarios(db)
            return render_template("eliminar_usuario.html", operacion="eliminar", usuarios=usuarios,
                seccion="usuarios",
                error="Error: No se encontró un usuario con ese RUT",
                rut=rut)

        usuario.eliminar_usuario(db, rut)
        return redirect("/usuarios")

    usuarios = usuario.obtener_usuarios(db)
    return render_template("eliminar_usuario.html", operacion="eliminar", usuarios=usuarios,
        seccion="usuarios")


# --- RUTAS PRESTAMO ---

@app.route("/prestamos")
def listar_prestamos():
    busqueda = request.args.get("busqueda", "")
    prestamos = prestamo.obtener_prestamos(db, busqueda)
    return render_template("prestamos.html", prestamos=prestamos, busqueda=busqueda, seccion="prestamos")


@app.route("/prestamos/crear", methods=["GET", "POST"])
def crear_prestamo():
    if request.method == "POST":
        isbn_copia = request.form["isbn_copia"]
        numero_copia = int(request.form["numero_copia"])
        usuario_rut = request.form["usuario_rut"]
        fecha_prestamo = request.form["fecha_prestamo"]
        fecha_devolucion = request.form["fecha_devolucion"]

        if not db.copia.find_one({"isbn": isbn_copia, "numero": numero_copia}):
            prestamos = prestamo.obtener_prestamos(db)
            return render_template("insertar_prestamo.html", operacion="crear", prestamos=prestamos,
                seccion="prestamos",
                error="Error: No se encontró esa copia",
                isbn_copia=isbn_copia, numero_copia=numero_copia,
                usuario_rut=usuario_rut, fecha_prestamo=fecha_prestamo,
                fecha_devolucion=fecha_devolucion)

        if not db.usuario.find_one({"rut": usuario_rut}):
            prestamos = prestamo.obtener_prestamos(db)
            return render_template("insertar_prestamo.html", operacion="crear", prestamos=prestamos,
                seccion="prestamos",
                error="Error: No se encontró un usuario con ese RUT",
                isbn_copia=isbn_copia, numero_copia=numero_copia,
                usuario_rut=usuario_rut, fecha_prestamo=fecha_prestamo,
                fecha_devolucion=fecha_devolucion)

        prestamo.insertar_prestamo(db, isbn_copia, numero_copia, usuario_rut, fecha_prestamo, fecha_devolucion)
        return redirect("/prestamos")

    prestamos = prestamo.obtener_prestamos(db)
    return render_template("insertar_prestamo.html", operacion="crear", prestamos=prestamos,
        seccion="prestamos")


@app.route("/prestamos/editar", methods=["GET", "POST"])
def editar_prestamo():
    if request.method == "POST":
        prestamo_id = request.form["prestamo_id"]
        datos = {
            "isbn_copia": request.form["isbn_copia"],
            "numero_copia": int(request.form["numero_copia"]),
            "usuario_rut": request.form["usuario_rut"],
            "fecha_prestamo": request.form["fecha_prestamo"],
            "fecha_devolucion": request.form["fecha_devolucion"]
        }
        prestamo.actualizar_prestamo(db, prestamo_id, datos)
        return redirect("/prestamos")

    isbn_copia = request.args.get("isbn_copia", "")
    numero_copia = request.args.get("numero_copia", "")
    usuario_rut = request.args.get("usuario_rut", "")
    fecha_prestamo = request.args.get("fecha_prestamo", "")
    prest = None
    error = None
    if isbn_copia and numero_copia and usuario_rut and fecha_prestamo:
        prest = db.prestamo.find_one({
            "isbn_copia": isbn_copia,
            "numero_copia": int(numero_copia),
            "usuario_rut": usuario_rut,
            "fecha_prestamo": fecha_prestamo
        })
        if not prest:
            error = "Error: No se encontró ese préstamo"

    prestamos = prestamo.obtener_prestamos(db)
    return render_template("editar_prestamo.html", operacion="editar", prestamos=prestamos,
        seccion="prestamos", prestamo=prest,
        isbn_copia=isbn_copia, numero_copia=numero_copia,
        usuario_rut=usuario_rut, fecha_prestamo=fecha_prestamo, error=error)


@app.route("/prestamos/eliminar", methods=["GET", "POST"])
def eliminar_prestamo_ruta():
    if request.method == "POST":
        isbn_copia = request.form["isbn_copia"]
        numero_copia = int(request.form["numero_copia"])
        usuario_rut = request.form["usuario_rut"]
        fecha_prestamo = request.form["fecha_prestamo"]

        prest = db.prestamo.find_one({
            "isbn_copia": isbn_copia,
            "numero_copia": numero_copia,
            "usuario_rut": usuario_rut,
            "fecha_prestamo": fecha_prestamo
        })

        if not prest:
            prestamos = prestamo.obtener_prestamos(db)
            return render_template("eliminar_prestamo.html", operacion="eliminar", prestamos=prestamos,
                seccion="prestamos",
                error="Error: No se encontró ese préstamo",
                isbn_copia=isbn_copia, numero_copia=numero_copia,
                usuario_rut=usuario_rut, fecha_prestamo=fecha_prestamo)

        prestamo.eliminar_prestamo(db, str(prest["_id"]))
        return redirect("/prestamos")

    prestamos = prestamo.obtener_prestamos(db)
    return render_template("eliminar_prestamo.html", operacion="eliminar", prestamos=prestamos,
        seccion="prestamos")


# --- RUTAS CONSULTAS ---

@app.route("/consultas/copias")
def consulta_copias():
    copias = consultas.consulta_copias(db)
    return render_template("consulta_copias.html", copias=copias, seccion="consultas")


@app.route("/consultas/prestamos-usuario")
def consulta_prestamos_usuario():
    rut = request.args.get("rut", "")
    resultados = []
    if rut:
        resultados = consultas.consulta_libros_por_usuario(db, rut)
    return render_template("consulta_prestamos.html", resultados=resultados, rut=rut, seccion="consultas")


if __name__ == "__main__":
    app.run(debug=True)
