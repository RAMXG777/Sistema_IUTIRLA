from sqlalchemy.orm import Session
import models

def registrar_tesis(
    db: Session, 
    titulo: str, 
    autor: str, 
    tutor: str, 
    carrera: str, 
    anio: int, 
    resumen: str, 
    cota_digital: str, 
    ruta_pdf: str
):
    nueva_tesis = models.Tesis(
        titulo=titulo,
        autor=autor,
        tutor=tutor,
        carrera=carrera,
        anio=anio,
        resumen=resumen,
        cota_digital=cota_digital,
        archivo_pdf=ruta_pdf
    )
    db.add(nueva_tesis)
    db.commit()
    db.refresh(nueva_tesis)
    return nueva_tesis

def buscar_tesis(db: Session, texto: str):
    patron = f"%{texto}%"
    return db.query(models.Tesis).filter(
        (models.Tesis.titulo.ilike(patron)) |
        (models.Tesis.autor.ilike(patron)) |
        (models.Tesis.carrera.ilike(patron)) |
        (models.Tesis.resumen.ilike(patron)) |
        (models.Tesis.cota_digital.ilike(patron))
    ).all()

def obtener_todas(db: Session):
    return db.query(models.Tesis).all()

def crear_solicitud(db: Session, tesis_id: int, nombre: str, cedula: str, correo: str):
    nueva_solicitud = models.SolicitudTesis(
        tesis_id=tesis_id,
        nombre_estudiante=nombre,
        cedula_estudiante=cedula,
        correo_estudiante=correo
    )
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    return nueva_solicitud

def obtener_solicitudes_pendientes(db: Session):
    return db.query(models.SolicitudTesis).filter(
        models.SolicitudTesis.estado == "pendiente"
    ).all()

def actualizar_tesis(
    db: Session, 
    tesis_id: int, 
    titulo: str, 
    autor: str, 
    tutor: str, 
    carrera: str, 
    anio: int, 
    resumen: str, 
    cota_digital: str
):
    tesis = db.query(models.Tesis).filter(models.Tesis.id == tesis_id).first()
    if not tesis:
        return None
    
    tesis.titulo = titulo
    tesis.autor = autor
    tesis.tutor = tutor
    tesis.carrera = carrera
    tesis.anio = anio
    tesis.resumen = resumen
    tesis.cota_digital = cota_digital
    
    db.commit()
    db.refresh(tesis)
    return tesis

# 7. Eliminar una tesis de la base de datos y su archivo físico
def eliminar_tesis(db: Session, tesis_id: int):
    tesis = db.query(models.Tesis).filter(models.Tesis.id == tesis_id).first()
    if not tesis:
        return None
    
    # Eliminar el archivo PDF del servidor si existe
    if tesis.archivo_pdf and os.path.exists(tesis.archivo_pdf):
        try:
            os.remove(tesis.archivo_pdf)
        except Exception as e:
            print(f"No se pudo eliminar el archivo físico: {e}")
            
    db.delete(tesis)
    db.commit()
    return tesis