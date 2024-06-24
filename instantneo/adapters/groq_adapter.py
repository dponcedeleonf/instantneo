from groq import Groq
import base64
##################TODO: Agregar modo JSON y prefill. Levantar error cuanfo skills aparezca como argumento, y pedir que se use json mode o prefill. O adaptar para que se use json mode, se tome la respuesta y se pase como args de la función y se ejecute.
class GroqAdapter:
    def __init__(self):
        self.client = None
    
    def initialize_client(self, api_key):
        # Solo inicializa el cliente si aún no se ha hecho
        if not self.client:
            self.client = Groq(api_key=api_key)
    
    #TODO: encode_image_to_base64 y get_media_type_from_extension están en el código para utilizarse cuando el API de Groq acepte imágenes.
    def encode_image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    
    def get_media_type_from_extension(self, img_path):
        # Determinar el tipo de medio a partir de la extensión del archivo
        extension = img_path.split('.')[-1].lower()
        if extension == "jpg" or extension == "jpeg":
            return "image/jpeg"
        elif extension == "png":
            return "image/png"
        elif extension == "gif":
            return "image/gif"
        elif extension == "webp":
            return "image/webp"
        else:
            raise ValueError("Formato de imagen no soportado.")
    
    def run(self, prompt, api_key, model, role_setup=None, temperature=0.5, max_tokens=1024, stop=None, presence_penalty=None, frequency_penalty=None, return_full_response=False, img=None, stream=False):
        """
        Ejecuta una solicitud al modelo de lenguaje de Groq.

        Args:
            prompt (str): El texto de entrada para el modelo.
            api_key (str): La clave de API de Groq.
            model (str): El nombre del modelo de Groq que se utilizará.
            role_setup (str, opcional): Descripción del Rol del agente
            temperature (float, opcional): El valor de temperatura para controlar la aleatoriedad de la respuesta (predeterminado: 0.5).
            max_tokens (int, opcional): El número máximo de tokens que se generarán en la respuesta (predeterminado: 1024).
            stop (str, opcional): Una secuencia de tokens que indicará al modelo que deje de generar respuestas.
            presence_penalty (float, opcional): Valor para controlar la probabilidad de repetir tokens.
            frequency_penalty (float, opcional): Valor para controlar la probabilidad de repetir tokens.
            return_full_response (bool, opcional): Si es True, devuelve el objeto de respuesta completo (predeterminado: False).
            img (str, opcional): La ruta del archivo de imagen que se incluirá en la solicitud.
            stream (bool, opcional): Si es True, transmitirá la respuesta en lugar de esperar a que se complete (predeterminado: False).

        Returns:
            str o dict: Si `return_full_response` es False, devuelve el texto de la respuesta. De lo contrario, devuelve el objeto de respuesta completo.
        """
        if img is not None:
            raise ValueError("El parámetro 'img' no es soportado por GroqAdapter.")

        # Inicializar el cliente de Groq si aún no se ha hecho
        self.initialize_client(api_key)

        # Crear una lista de mensajes para la solicitud
        messages = []

        # Agregar el texto de entrada como un mensaje
        messages.append({"role": "user", "content": prompt})

        # Crear los parámetros de la solicitud
        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }

        # Si se proporciona un rol, agregarlo como un mensaje de sistema
        if role_setup:
            messages.insert(0, {"role": "system", "content": role_setup})

        # Si se proporciona una secuencia de detención, agregarla a los parámetros de la solicitud
        if stop:
            request_params["stop"] = stop

        # Si se proporcionan valores de presence_penalty y frequency_penalty, agregarlos a los parámetros de la solicitud
        if presence_penalty is not None:
            request_params["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            request_params["frequency_penalty"] = frequency_penalty

        # Obtener la respuesta del modelo
        response = self.client.chat.completions.create(**request_params)

        # Si se requiere la respuesta completa, devolver el objeto de respuesta
        if return_full_response:
            return response
        # Si solo se requiere el texto de la respuesta
        else:
            # Devolver el texto de la respuesta obtenido del objeto de respuesta
            return response.choices[0].message.content
