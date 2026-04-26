# Objetivo

Diseño multi diagrama del Modelo Dimensional para facilitar el diseño y entendimiento cuando los diagramas se hacen demasiado extensos y complejos.

# Requerimientos

- Un modelo debe poder tener submodelo o diagramas del modelo conceptual. Siempre debe haber un diagrama principal del modelo dimensional que contenga todas las tablas de hechos y dimensiones. Los submodelos deben contener solo un subconjunto de tablas de hechos y dimensiones.
- Los submodelos deben ser visualmente distintos del modelo principal (ej. color de fondo, borde, etc.)
- Debo poder crear, editar, eliminar submodelos.
- Debo poder arrastrar y soltar tablas de hechos y dimensiones entre submodelos.
- Debo poder arrastrar y soltar tablas de hechos y dimensiones entre submodelos.
- Cada diagrama tiene los objetos visuales (tablas de hechos y dimensiones) y estos referencian a los objetos que contiene la información de las tablas (hechos y dimensiones). Por lo tanto, si modifico un objeto en un diagrama, se modificará en todos los diagramas que lo referencien.
- Un click en el canvas de un diagrama debe activar el panel lateral permitiendo cambiar el nombre del diagrama y la descripcion (campo texto/text area extenso con posibilidad de visualización en formato Markdown)