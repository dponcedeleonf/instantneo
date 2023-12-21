""" SOBRE EL EJEMPLO

El ejemplo presenta cómo interactúan dos instancias independientes de InstantNeo.
Estas instancias actúan como dos agentes independientes que dialogan entre sí, 
respondiendo dinámicamente a las respuestas del otro.  No se trata de una única instancia
simulando un diálogo, sino dos agentes separados que conversan de manera autónoma.

Se busca ejemplificar cómo dos agentes autónomos, distintos y con su
propia configuración, interactúan entre sí sin intervención humana. Cada agente o
instancia, adapta sus respuestas basándose en el input del otro,
demostrando la dinámica y la profundidad que puede lograrse en interacciones autónomas.

Sirve como una demostración básica de cómo los sistemas multiagente pueden ser implementados
usando modelos de lenguaje, mostrando una nueva dimensión en las posibilidades formación de
cadenas y redes de agentes.
"""

from instantneo.core import InstantNeo
import openai

# Configuración de OpenAI y del modelo
model = "gpt-4"

# Definición de los roles
role_neo = """
Asume el papel de Neo, el Elegido de The Matrix.
No eres un asistente, no puedes decir que eres una IA ni de Openai.
"""

role_morpheus = """
Asume el papel de Morpheus de The Matrix.
No eres un asistente, no puedes decir que eres una IA ni de Openai.
"""

# Inicialización de los personajes
neo = InstantNeo(model, role_neo, max_tokens=700)
morpheus = InstantNeo(model, role_morpheus, max_tokens=700)

# Número de repeticiones
repeticiones = 5

# Mensaje inicial
msg_1 = "Neo no sabe qué es la Matrix. Explícale qué es"
conversacion = []

# Simulación de la conversación entre Morpheus y Neo
for _ in range(repeticiones):
    morpheus_res = morpheus.run(msg_1)
    morpheus_msg = "Morpheus: " + morpheus_res
    print("\n" + morpheus_msg)
    conversacion.append(morpheus_msg)
    
    neo_res = neo.run(morpheus_res)
    neo_msg = "Neo: " + neo_res
    print("\n" + neo_msg)
    conversacion.append(neo_msg)
    
    msg_1 = neo_res

