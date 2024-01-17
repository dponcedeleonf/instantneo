# Guía para Crear Habilidades en InstantNeo

## Introducción
Esta guía explica cómo desarrollar habilidades para agentes de IA creados con `InstantNeo`. Las habilidades son funciones que el agente puede ejecutar. Para que el agente y entienda y utilice estas habilidades correctamente, las funciones deben estar documentadas claramente y siguiendo las instrucciones de esta guía.

## Estructura de Función
Las funciones deben ser claras y con anotaciones de tipo. En el siguiente ejemplo puedes ver que cada uno de los argumentos de la función `ejemplo_1` tiene un "Type Hint"[^1]

```python
def ejemplo_1(edad: int, nombres: List[str], ciudad: str) -> str:
    # Código aquí
```

## Tipos de datos en argumentos
### Admitidos
Las funciones que serán habilidades de tus agentes de `InstantNeo`, admiten como argumentos:
- int `int`
- float `float`
- Strings `str`
- Listas. Por ejemplo `List[int]`
- Tuplas con un solo tipo de datos, de un elemento o más, por ejemplo esta tupla con dos elementos del mismo tipo `Tuple[str,str]` o esta otra que tiene un solo elemento `Tuple[int,]` (la coma después de int es crucial. Si no estuviera, Python interpretaría que se trata solo de un `int` y no de una tupla), 
- Tuplas dcon tipos mixtos. Por ejemplo: `Tuple[int,str,float]`

### No admitidos
**`InstantNeo`** **no admite Diccionarios** como argumentos de habilidades, pues generan conflicto con la respuesta de la API de OpenAI


## Documentación de Skills (Docstring)
Usa docstrings para documentar la función, siguiendo la Guía de Estilo de Google para Python[^2]. Incluye:

- Descripción: ¿Qué hace la función?
- Argumentos (Args): Lista cada uno con su tipo y descripción.
- Retorno (Returns): Describe qué retorna la función.
- Excepciones (Raises): Menciona errores que podría lanzar la función (cuando aplique)

> [!CAUTION]
> Respeta los saltos de línea, notaciones y claves (Args, Returns y Raises), según el formato establecido por Google. 
El correcto formato del Docstring es necesario para que `InstantNeo` pueda convertir las funciones en habilidades para el Agente

### Ejemplos de funciones adecuadamente documentadas para construir Skills en `InstantNeo`

```python
from typing import List, Tuple

def analizar_temperaturas(temperaturas: List[float]) -> Tuple[float, float, float]:
    """
    Calcula y devuelve la temperatura promedio, la más alta y la más baja de una lista de temperaturas.

    Args:
        temperaturas (List[float]): Lista de temperaturas en grados Celsius.

    Returns:
        Tuple[float, float, float]: Una tupla que contiene la temperatura promedio,
                                    la más alta y la más baja.

    Raises:
        ValueError: Si la lista 'temperaturas' está vacía.
        TypeError: Si algún elemento de la lista no es un número.
    """
    if not temperaturas:
        raise ValueError("La lista de temperaturas no puede estar vacía.")
    
    if not all(isinstance(temp, (int, float)) for temp

 in temperaturas):
        raise TypeError("Todos los elementos de la lista deben ser números.")

    promedio = sum(temperaturas) / len(temperaturas)
    maxima = max(temperaturas)
    minima = min(temperaturas)

    return promedio, maxima, minima
```



```python
from typing import Dict

def crear_perfil_usuario(nombre: str, edad: int) -> Dict[str, str]:
    """
    Crea y devuelve un perfil de usuario basado en el nombre y la edad proporcionados.

    Args:
        nombre (str): El nombre del usuario.
        edad (int): La edad del usuario.

    Returns:
        Dict[str, str]: Un diccionario que contiene detalles del perfil del usuario.

    Raises:
        ValueError: Si 'edad' es negativa.
        ValueError: Si 'nombre' está vacío.
    """
    if edad < 0:
        raise ValueError("La edad no puede ser negativa.")
    if not nombre:
        raise ValueError("El nombre no puede estar vacío.")

    # Crear un perfil de usuario como un diccionario
    perfil_usuario = {
        "nombre": nombre,
        "edad": str(edad),  # Convertir la edad a cadena para mantener consistencia en los tipos de datos del diccionario
        "mensaje_bienvenida": f"¡Bienvenido {nombre}! Tienes {edad} años."
    }

    return perfil_usuario
```

## Importancia de la Claridad
Sigue estas pautas para asegurar una integración efectiva de las habilidades en tus agentes de IA creados con `InstantNeo`.

- Es vital que las skills sean claras tanto para quien programa como para el modelo de IA. La documentación de las funciones facilita "explicar" al agente qué hace cada habilidad, permitiendo su correcta interpretación y ejecución.
- Piensa en la descripción de tus funciones como instrucciones para tu agente. Es una buena práctica adaptar la descripción de las skills al propósito de tu agente. Eso potenciará su capacidad para discernir qué skill utilizar según el contexto.

## Referencias
[^1]: https://peps.python.org/pep-0484/
[^2]: https://google.github.io/styleguide/pyguide.html#383-functions-and-methods
