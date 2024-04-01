from anthropic import Anthropic
import base64

class ClaudeAdapter:
    def __init__(self):
        self.client = None
    
    def initialize_client(self, api_key):
        # Solo inicializa el cliente si aún no se ha hecho
        if not self.client:
            self.client = Anthropic(api_key=api_key)
    
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
    
    def run(self, prompt, api_key, model, role_setup=None, temperature=1.0, max_tokens=500, stop=None, presence_penalty=None, frequency_penalty=None, return_full_response=False, img=None, stream=False):
        """
        Ejecuta una solicitud al modelo de lenguaje de Anthropic.

        Args:
            prompt (str): El texto de entrada para el modelo.
            api_key (str): La clave de API de Anthropic.
            model (str): El nombre del modelo de Anthropic que se utilizará.
            role_setup (str, opcional): Una descripción del rol que desempeñará el modelo.
            temperature (float, opcional): El valor de temperatura para controlar la aleatoriedad de la respuesta (predeterminado: 1.0).
            max_tokens (int, opcional): El número máximo de tokens que se generarán en la respuesta (predeterminado: 500).
            stop (str, opcional): Una secuencia de tokens que indicará al modelo que deje de generar respuestas.
            presence_penalty (float, opcional): Valor para controlar la probabilidad de repetir tokens.
            frequency_penalty (float, opcional): Valor para controlar la probabilidad de repetir tokens.
            return_full_response (bool, opcional): Si es True, devuelve el objeto de respuesta completo (predeterminado: False).
            img (str, opcional): La ruta del archivo de imagen que se incluirá en la solicitud.
            stream (bool, opcional): Si es True, transmitirá la respuesta en lugar de esperar a que se complete (predeterminado: False).

        Returns:
            str o dict: Si `return_full_response` es False, devuelve el texto de la respuesta. De lo contrario, devuelve el objeto de respuesta completo.
        """

        # Inicializar el cliente de Anthropic si aún no se ha hecho
        self.initialize_client(api_key)

        # Crear una lista de mensajes para la solicitud
        messages = []

        # Si se proporciona una imagen, agregar la imagen y el texto de entrada como un mensaje
        if img:
            media_type = self.get_media_type_from_extension(img)
            img_data = self.encode_image_to_base64(img)
            messages.append({"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}},
                {"type": "text", "text": prompt}
            ]})
        # Si no se proporciona una imagen, agregar solo el texto de entrada como un mensaje
        else:
            messages.append({"role": "user", "content": prompt})

        # Crear los parámetros de la solicitud
        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        # Si se proporciona un rol, agregarlo a los parámetros de la solicitud
        if role_setup:
            request_params["system"] = role_setup

        # Si se proporciona una secuencia de detención, agregarla a los parámetros de la solicitud
        if stop:
            request_params["stop_sequences"] = [stop]

        # Si se solicita la transmisión de la respuesta y no se requiere la respuesta completa
        if stream and not return_full_response:
            response_text = ""
            # Transmitir la respuesta y concatenar las partes de texto a medida que se reciben
            with self.client.messages.stream(**request_params) as stream_manager:
                for text in stream_manager.text_stream:
                    response_text += text
            return response_text

        # Si no se solicita la transmisión de la respuesta
        else:
            # Obtener la respuesta completa del modelo
            response_message = self.client.messages.create(**request_params)

            # Si se requiere la respuesta completa, devolver el objeto de respuesta
            if return_full_response:
                #print(response_message)
                return response_message
            # Si solo se requiere el texto de la respuesta
            else:
                #print(response_message)
                # Devolver el texto de la respuesta obtenido del objeto de respuesta
                return response_message.content[0].text
