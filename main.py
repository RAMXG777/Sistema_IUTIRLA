import os
import shutil
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import crud
import models
from database import engine, get_db
from email_service import enviar_tesis_por_correo

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Control y Búsqueda de Tesis - IUTIRLA", version="1.0.0"
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def inicio():
    ruta_index = os.path.join("static", "index.html")
    if os.path.exists(ruta_index):
        return FileResponse(ruta_index, media_type="text/html")
    return {
        "mensaje": "Servidor de Control de Tesis activo",
        "estado": "Base de datos sincronizada y directorio estático montado",
    }


@app.post("/tesis/registrar")
def registrar_nueva_tesis(
    titulo: str = Form(...),
    autor: str = Form(...),
    tutor: str = Form(...),
    carrera: str = Form(...),
    anio: int = Form(...),
    resumen: str = Form(...),
    cota_digital: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not archivo.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    os.makedirs("uploads", exist_ok=True)
    nombre_seguro = os.path.basename(archivo.filename)
    ruta_pdf = os.path.join("uploads", nombre_seguro)

    try:
        with open(ruta_pdf, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)

        return crud.registrar_tesis(
            db=db,
            titulo=titulo.strip(),
            autor=autor.strip(),
            tutor=tutor.strip(),
            carrera=carrera.strip(),
            anio=anio,
            resumen=resumen.strip(),
            cota_digital=cota_digital.strip(),
            ruta_pdf=ruta_pdf.replace("\\", "/"),
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Ya existe una tesis registrada con esa Cota Digital.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al registrar la tesis: {str(e)}"
        )


@app.get("/tesis/buscar")
def buscar_tesis_en_catalogo(texto: str = "", db: Session = Depends(get_db)):
    if not texto.strip():
        return crud.obtener_todas(db)
    return crud.buscar_tesis(db, texto.strip())


@app.get("/tesis/ver/{tesis_id}")
def ver_pdf_tesis(tesis_id: int, db: Session = Depends(get_db)):
    tesis = db.query(models.Tesis).filter(models.Tesis.id == tesis_id).first()
    if not tesis:
        raise HTTPException(status_code=404, detail="Tesis no encontrada")

    ruta_pdf = tesis.archivo_pdf
    if not ruta_pdf or not os.path.exists(ruta_pdf):
        raise HTTPException(
            status_code=404, detail="Archivo PDF no encontrado en el servidor"
        )

    return FileResponse(
        path=ruta_pdf,
        media_type="application/pdf",
        filename=os.path.basename(ruta_pdf),
    )


@app.post("/solicitudes/crear")
def pedir_tesis(
    tesis_id: int = Form(...),
    nombre: str = Form(...),
    cedula: str = Form(...),
    correo: str = Form(...),
    db: Session = Depends(get_db),
):
    tesis = db.query(models.Tesis).filter(models.Tesis.id == tesis_id).first()
    if not tesis:
        raise HTTPException(status_code=404, detail="La tesis solicitada no existe")
    return crud.crear_solicitud(db, tesis_id, nombre.strip(), cedula.strip(), correo.strip())


@app.post("/solicitudes/aprobar/{solicitud_id}")
def aprobar_y_enviar(solicitud_id: int, db: Session = Depends(get_db)):
    solicitud = (
        db.query(models.SolicitudTesis)
        .filter(models.SolicitudTesis.id == solicitud_id)
        .first()
    )
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    exito = enviar_tesis_por_correo(
        correo_destino=solicitud.correo_estudiante,
        nombre_estudiante=solicitud.nombre_estudiante,
        titulo_tesis=solicitud.tesis.titulo,
        ruta_pdf=solicitud.tesis.archivo_pdf,
    )

    if exito:
        solicitud.estado = "enviado"
        db.commit()
        return {"mensaje": "Tesis enviada con éxito al correo del estudiante"}
    else:
        raise HTTPException(
            status_code=500, detail="Error al enviar el correo electrónico"
        )


@app.put("/tesis/actualizar/{tesis_id}")
def actualizar_registro_tesis(
    tesis_id: int,
    titulo: str = Form(...),
    autor: str = Form(...),
    tutor: str = Form(...),
    carrera: str = Form(...),
    anio: int = Form(...),
    resumen: str = Form(...),
    cota_digital: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        tesis_actualizada = crud.actualizar_tesis(
            db=db,
            tesis_id=tesis_id,
            titulo=titulo.strip(),
            autor=autor.strip(),
            tutor=tutor.strip(),
            carrera=carrera.strip(),
            anio=anio,
            resumen=resumen.strip(),
            cota_digital=cota_digital.strip(),
        )
        if not tesis_actualizada:
            raise HTTPException(status_code=404, detail="Tesis no encontrada")
        return {"mensaje": "Tesis actualizada con éxito", "tesis": tesis_actualizada}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Esa Cota Digital ya está en uso por otra tesis."
        )


@app.delete("/tesis/eliminar/{tesis_id}")
def eliminar_registro_tesis(tesis_id: int, db: Session = Depends(get_db)):
    tesis_eliminada = crud.eliminar_tesis(db=db, tesis_id=tesis_id)
    if not tesis_eliminada:
        raise HTTPException(status_code=404, detail="Tesis no encontrada")
    return {"mensaje": "Tesis eliminada con éxito"}
