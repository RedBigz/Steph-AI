import yamlfile, os

class Personality:
    def __init__(self, path) -> None:
        self.path_character = os.path.join(path, "character.yaml")
        self.path_image = os.path.join(path, "image.yaml")
        
        # Parse Character
        self.name: str = yamlfile.get_attr(self.path_character, "name")
        self.ctx: str = yamlfile.get_attr(self.path_character, "context")

        # Parse Image Prompts
        self.character_prompt: str = yamlfile.get_attr(self.path_image, "character-prompt")
        self.character_negative_prompt: str = yamlfile.get_attr(self.path_image, "character-negative-prompt")
        self.ai_intensity: float = yamlfile.get_attr(self.path_image, "ai-intensity")