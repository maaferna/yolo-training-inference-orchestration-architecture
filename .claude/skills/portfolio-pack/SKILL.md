---
name: portfolio-pack
description: Genera y mantiene el material de portafolio derivado de esta arquitectura — viñetas de CV, descripción de LinkedIn, ficha de proyecto, guion de entrevista y textos para los visuales. Usar cuando se pida contenido para portafolio, currículum, LinkedIn, una ficha de proyecto, adaptar el material a una oferta concreta, o preparar cómo presentar el repositorio.
---

# Paquete de portafolio

## Material existente

- `docs/portfolio/PORTFOLIO_RESUME_CONTENT.md` — viñetas por perfil (ML, Backend/Plataforma, CV),
  descripción de LinkedIn, descripción de GitHub, ficha de proyecto.
- `docs/portfolio/PORTFOLIO_IMPLEMENTATION_GUIDE.md` — dónde y cómo usar cada pieza.
- `assets/diagrams/`, `assets/poster/` — visuales listos para incrustar.

Antes de escribir nada nuevo, leer ambos documentos. Adaptar una viñeta existente casi siempre
supera a inventar una desde cero.

## Los tres perfiles

El material se organiza por el puesto al que se aplica. Elegir el ángulo antes de escribir:

| Perfil | Qué enfatizar |
|---|---|
| **ML Engineer** | Multi-seed y selección por validación, gestión de memoria CUDA, seguimiento de experimentos, entrenamiento incremental con umbral de mejora |
| **Backend / AI Platform** | Separación de servicios, frontera HTTP entre web y cómputo, contrato de artefactos, propagación de errores, roadmap por evidencia operativa |
| **Computer Vision** | SAHI y detección de objetos pequeños, compromiso tamaño de tile / solape / coste, generación de dataset sintético con SAM, formatos COCO y YOLO |

## Anatomía de una viñeta

```
<Verbo de diseño> <qué> <con qué restricción técnica>, <resultado cualitativo>;
<segundo detalle técnico que demuestra profundidad>
```

Verbos válidos: *Designed, Architected, Documented, Engineered, Specified, Evaluated*.
Evitar *Built, Shipped, Deployed, Launched*: este repositorio documenta arquitectura, y la
implementación privada no es demostrable públicamente. Sobrevender es el riesgo principal.

## Regla de las cifras

Este es el punto más delicado del repositorio y donde hay que ser estricto.

El README declara que no contiene métricas reales. Las viñetas actuales incluyen cifras como
"reducing OOM incidents by 80%" o "~60% cost reduction" que **no** están respaldadas por ningún
dato publicable. Un revisor que compare ambas cosas encuentra una contradicción.

Al escribir o revisar viñetas:

- Preferir resultados cualitativos: *"eliminando fallos por OOM durante el entrenamiento
  multi-seed"* en lugar de un porcentaje.
- Si el usuario tiene una cifra real de su trabajo privado y quiere usarla en el CV, es legítimo
  en el CV, pero **no debe aparecer en el repositorio público** ni en los diagramas.
- Toda cifra que quede en el repositorio se marca como ilustrativa.

Señalar esta contradicción cuando se detecte, en lugar de propagarla.

## Cómo enmarcar el proyecto

El repositorio es una **pieza de diseño de sistemas**, no un producto entregado. La forma honesta
y más fuerte de presentarlo:

> Documentación de arquitectura public-safe de una plataforma interna de visión por computador:
> separación entre orquestación web y cómputo GPU, entrenamiento y inferencia YOLO/SAHI,
> seguimiento de experimentos y una hoja de ruta de evolución guiada por evidencia operativa
> en lugar de por infraestructura por defecto.

Lo que distingue este proyecto en una revisión técnica no es la lista de tecnologías, sino:

1. **Restricción deliberada.** Justifica *no* usar Kubernetes, colas ni workers, con los
   disparadores concretos que cambiarían la decisión.
2. **Riesgos declarados.** Documenta explícitamente la ejecución síncrona, el acoplamiento al
   sistema de ficheros compartido, la condición de carrera en la referencia del mejor modelo y
   la contención de GPU.
3. **Coste como decisión de arquitectura.** El análisis local / AWS / híbrido razona sobre
   volumen de datos y horas de GPU, no sobre preferencias.

Estos tres puntos son el guion de entrevista. Conducen a la conversación que el repositorio
puede ganar.

## Al terminar

Si el material nuevo entra en el repositorio, ejecutar la skill `public-safe-audit`.
Si necesita apoyo visual, usar `diagram-studio`.
