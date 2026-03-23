import os
from anthropic import Anthropic, RateLimitError, APIConnectionError, APIError
from settings import settings


class ClaudeService():
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE


        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0


    def generate(
        self,
        prompt: str,
        model: Optional[str]=None,
        max_tokens: Optional[int]=None,
        temperature: Optional[float]=None,
        max_retries: int=3,
    ) -> str:


        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature


        for attempt in range(max_retries):
            try:
                req_params = {


                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages":[
                        {"role":"user", "content":prompt}
                    ]
                }
                response = self.client.messages.create(**req_params)


                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens
                self.request_count += 1


                return response.content[0].text
            except RateLimitError as e:
                if attempt <= max_retries -1:
                    wait_time = (2 ** attempt)*1
                    print(f"Rate limit hit. Waiting {wait_time} before retry {attempt}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    raise APIError(f"Rate limit exceeded after {max_retries} retries") from e
            
            except APIConnectionError as e:
                if attempt <= max_retries -1:
                    wait_time = (2 ** attempt) * 1
                    print(f"Connection error. Retrying in {wait_time} minutes...attempt {attempt}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    raise APIError(f"Connection failed after {max_retries} attempts") from e
            
            except Exception as e:
                raise Exception(f"Claude API Error: {str(e)}") from e
        # raise APIError("Failed to get response from Claude") from e





