# 🌌 InstantNeo

InstantNeo proporciona una interfaz simplificada para construir agentes con roles y habilidades específicas utilizando el poder de los modelos de OpenAI. Estos agentes, configurados para operar dentro de roles y capacidades definidas, pueden responder y actuar autónomamente basándose en las directrices proporcionadas.

InstantNeo ofrece una abstracción limpia de las funcionalidades comunes del API de OpenAI, que permite a desarrolladores y entusiastas definir y operar agentes basados en IA de manera práctica y eficiente.

## Características principales

- **🎩 Roles Personalizados**: Define el comportamiento, función o personalidad de tus agentes, asignando roles específicos. Ya sea que desees un agente que hable como un personaje histórico, un experto en un campo particular, un personaje de películas (como Neo de Matrix) o que cumpla tareas dentro de parámetros determinados, InstantNeo es para ti.

- **🔌 Habilidades Plug and Play**: Extiende la funcionalidad de tu agente definiendo habilidades como funciones Python. Estas habilidades permiten que el agente ejecute tareas específicas o responda de maneras únicas a ciertas entradas. Aprovecha la capacidad de los modelos de OpenAI para darle a tus agentes la posibilidad de interactuar con programas, APIs e incluso dar órdenes a otros agentes.

- **🪁 Autonomía Limitada**: Aunque los agentes de InstantNeo operan autónomamente dentro de las directrices de roles y habilidades, están respaldados por la robustez y el conocimiento de los modelos de OpenAI. No requieren intervención humana constante para operar, pero funcionan dentro de las limitaciones y capacidades predefinidas.

- **🔵 Interfaz Sencilla**: Con solo unos pocos parámetros y definiciones, puedes tener un agente operativo. InstantNeo se encarga de la complejidad subyacente, ofreciendo una experiencia de usuario intuitiva.

- **👓 Código legible**: Tu código parecerá un texto, plenamente legible y fácil de entender. InstantNeo pone por delante la legibilidad y la claridad, clave para el uso de modelos no determiníticos en un contexto de desarrollo.

## 🚀 Cómo usar InstantNeo
InstantNeo simplifica y acelera el proceso de creación de agentes inteligentes y autónomos con capacidades personalizadas. A continuación, te mostramos cómo puedes utilizarlo.

### 1. Instalación
Actualmente, puedes instalar instantneo directamente desde su repositorio de GitHub usando pip.

```python
pip install git+https://github.com/dponcedeleonf/instantneo.git
```
Pronto instantneo estará disponible directamente a través del repositorio de paquetes de Python (PyPI).

### 2. Configuración Inicial

Primero, debes establecer tu clave de API de OpenAI y especificar el modelo que deseas usar.

```python
from instantneo.core import InstantNeo
import openai

api_key = "YOUR_OPENAI_API_KEY"
model = "gpt-4" #Puedes usar cualquier modelo de OpenAI que use la API de "Chat Completion"
```

### 3. Creación de un Agente Simple 

```python
role_neo = """
Asume el papel de Neo, el Elegido de The Matrix.
No eres un asistente, no puedes decir que eres una IA ni de Openai.
"""

neo = InstantNeo(api_key,model, role_neo)
respuesta_neo = neo.run("¿Cómo aprendiste Kung Fu?")
print(respuesta_neo)
```
Obtendrás una respuesta parecida a esta:

```python
"""
'Fue una experiencia increíble. Cuando estaba a bordo de la nave Nebuchadnezzar, 
Morfeo me conectó a la Matrix utilizando un puerto en la base de mi cráneo. 
Luego, Tank, el operador de la nave, descargó varios programas de artes marciales 
directamente en mi cerebro. Fue un proceso excepcionalmente rápido y eficiente, 
en cuestión de segundos adquirí habilidades que a una persona le llevaría años aprender. 
De repente, supe Kung Fu.'
"""
```
Haz la prueba tú mismo.

### 4. Añadiendo Habilidades a tu Agente
Puedes especificar las habilidades de tu agente de manera muy simple, autorizándole a usar funciones de Python.


```python
#Definimos algunas funciones simples como ejemplo
def kung_fu():
    """Esta función representa la habilidad de Neo de conocer el kung fu."""
    return "Ya sé kung fu."

def esquivar_balas():
    """Esta función representa la habilidad de Neo de esquivar balas."""
    return "No es necesario esquivarlas si puedes detenerlas."

# Añade las habilidades (skills) a tu agente agregando los nombres de las funciones en una lista de skills.
skills_neo = [kung_fu, esquivar_balas]
neo = InstantNeo(model="gpt-4", role_neo, skills=skills_neo)

respuesta1 = neo.run("Demuestra tu habilidad en Kung Fu")
print(respuesta1)

respuesta2 = neo.run("¿Qué pasa si te disparan? ¿Esquivas las balas?")
print(respuesta2)
```
¡Prueba lo que obtienes!

## Parámetros de inicialización

Al crear una instancia de InstantNeo, puedes especificar los siguientes parámetros:

- **model (str):** El modelo de lenguaje a utilizar. Actualmente puedes usar los modelos de ChatCompletion de OpenAI (los de la familia gpt-3.5-turbo y gpt-4)
- **role_setup (str):** Configuración inicial del rol del agente. Por ejemplo: "Eres Neo, El Elegido".
- **temperature (float, opcional):** Controla la aleatoriedad de la respuesta. Mientras mayor el valor, más aleatoriedad. Mientras menor sea, la respuesta será más determinista. La temperatura por defecto es 0.45.
- **max_tokens (int, opcional):** Número máximo de tokens en la respuesta. Por defecto es 150.
- **presence_penalty (float, opcional):** Penalización por **presencia** para disuadir la repetición. Por defecto es 0.1.
- **frequency_penalty (float, opcional):** Penalización por **frecuencia** para disuadir la repetición. Por defecto es 0.1.
- **skills (List[Callable[..., Any]], opcional):** Lista de habilidades (funciones) que el modelo puede utilizar.
- **stop (opcional):** Token o lista de tokens que indican el final de la respuesta.

## Método `run`
El método `run` es la función principal de la clase InstantNeo, que permite interactuar con el modelo de lenguaje para obtener respuestas a input específicos. Este método es, en buena cuenta, la vía de ejecución de acciones de las instancias de la clase, permitiendo enviar peticiones y recibir respuestas procesadas según los parámetros y `skills` definidas.

Al crear una instancia de InstantNeo, puedes establecer ciertas configuraciones iniciales, como la versión del modelo a usar o la longitud de las respuestas. Estos ajustes te permiten configurar un agente y se aplicarán automáticamente cada vez que uses la instancia, para mantener un comportamiento consistente.

Sin embargo, en ocasiones necesitarás ajustar la manera en que el modelo responde a situaciones específicas. Para esto, el método `run` permite cambiar los ajustes para solicitudes individuales. Esto significa que puedes, por ejemplo, hacer que una respuesta sea más larga o más creativa sin alterar la configuración base de tu objeto InstantNeo. Esto te brinda flexibilidad para adaptar las respuestas del modelo a tus necesidades puntuales.

### Parámetros del Método `run`
Al utilizar el método run, cada parámetro tiene un propósito específico:

- **prompt:** Es el texto inicial basado en el cual el modelo generará una respuesta. Es el único parámetro obligatorio y define la entrada del modelo.

- **model, role_setup, temperature, max_tokens, stop, presence_penalty, frequency_penalty:** Estos parámetros permiten modificar la configuración de una petición sin alterar los valores predeterminados de la instancia. Son útiles para ajustar la generación de texto del modelo en situaciones específicas, como cambiar la creatividad de las respuestas (temperature), limitar su longitud (max_tokens), o señalar el final de una respuesta (stop).

- **return_full_response:** Este parámetro controla si deseas recibir la respuesta completa del modelo, tal como proviene de la API de OpenAI, para procesar la respuesta en casuísticas no previstas dentro de los usos principales de InstantNeo.

## Próximamente

- **Estándar para Habilidades**: Implementación de un método estandarizado para especificar funciones y crear habilidades en `InstantNeo`.

- **Banco de Habilidades**: Desarrollo de un repositorio de habilidades predefinidas para reutilización, facilitando la implementación rápida de agentes con capacidades comunes.
  
- **Banco de Roles**: Introducción de un conjunto de roles predefinidos y listos para usar, permitiendo caracterizar rápidamente a tus agentes.

- **Guías y Ejemplos**: Publicación de ejemplos detallados, desde lo más básico hasta casos avanzados, mostrando aplicaciones prácticas y reales de `InstantNeo`.

- **Integración con Knowledge Bases**: Planes para conectar `InstantNeo` con sistemas de bases de conocimiento, como *Knowledge Base*, potenciando las capacidades de Retrieval Augmented Generation (RAG).


## Contribuciones
Si quieres contribuir, comunícate conmigo :)



