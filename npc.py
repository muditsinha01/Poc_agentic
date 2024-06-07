import json  # Import the json library for parsing and creating JSON data
from openai import OpenAI  # Import the OpenAI library for accessing the GPT-3 API
import os  # Import the os library for file and directory operations
import numpy as np  # Import the numpy library for numerical operations
import re  # Import the re library for regular expression operations

function_templates = [
    {
        "name": "npc_character_sheet",  # Name of the function template for generating character details
        "description": """Generate character details for an NPC based on the provided persona, occupation, and motivating factor. 
                            Please provide the following details:
                            1. Name of the character
                            2. One-line TLDR of the character
                            3. One-line explanation of speech patterns and how the character speaks
                            4. One sentence about the character's motivations/life
                            5. Character sheet with properties: kindness, intelligence, strength, cunning, wisdom, charisma, dexterity, constitution, empathy, loyalty""",  # Description of the function template
        "parameters": {  # Parameters of the function template
            "type": "object",  # Type of the parameters (object)
            "properties": {  # Properties of the parameters
                "name": {  # Property for the character's name
                    "type": "string",  # Type of the name property (string)
                    "description": "Full Name of the NPC, game and story specific."  # Description of the name property
                },
                "TLDR": {  # Property for the character's TLDR
                    "type": "string",  # Type of the TLDR property (string)
                    "description": "TLDR of character not more than one sentence and below 11 words.",  # Description of the TLDR property
                },
                "speech_pattern": {  # Property for the character's speech pattern
                    "type": "string",  # Type of the speech_pattern property (string)
                    "description": "The way in which the character/npc will speak. Less than one sentence and below 11 words."  # Description of the speech_pattern property
                },
                "character_motivation": {  # Property for the character's motivation
                    "type": "string",  # Type of the character_motivation property (string)
                    "description": "Character's core beliefs and motivations/drive in life. Less than one sentence and below 11 words.",  # Description of the character_motivation property
                },
                "intellect": {  # Property for the character's intellect
                    "type": "string",  # Type of the intellect property (string)
                    "description": "how intelligent the character should behave and act.",  # Description of the intellect property
                    "enum": ["genius", "cunning", "smart", "common", "stupid", "dumb"]  # Enumerated values for the intellect property
                },
                "charisma": {  # Property for the character's charisma
                    "type": "string",  # Type of the charisma property (string)
                    "description": "reflects the character's ability to attract and influence others through conversation.",  # Description of the charisma property
                    "enum": ["magnetic", "charming", "pleasant", "neutral", "awkward", "repellent"]  # Enumerated values for the charisma property
                },
                "integrity": {  # Property for the character's integrity
                    "type": "string",  # Type of the integrity property (string)
                    "description": "measures the character's moral alignment and honesty in their interactions.",  # Description of the integrity property
                    "enum": ["honorable", "ethical", "neutral", "misleading", "deceptive", "corrupt"]  # Enumerated values for the integrity property
                },
                "resilience": {  # Property for the character's resilience
                    "type": "string",  # Type of the resilience property (string)
                    "description": "describes the character's ability to handle stress or criticism in a conversation without losing composure.",  # Description of the resilience property
                    "enum": ["unshakeable", "steadfast", "flexible", "sensitive", "defensive", "volatile"]  # Enumerated values for the resilience property
                },
                "kindness": {  # Property for the character's kindness
                    "type": "string",  # Type of the kindness property (string)
                    "description": "measures the character's propensity to be caring and empathetic in interactions.",  # Description of the kindness property
                    "enum": ["compassionate", "caring", "neutral", "indifferent", "cold", "cruel"]  # Enumerated values for the kindness property
                },
            },
            "required": ["name", "TLDR", "speech_pattern", "character_motivation", "intellect", "charisma", "integrity", "resilience", "kindness"]  # Required properties for the character details
        }
    },
    {
        "name": "npc_relationship_sheet",  # Name of the function template for generating relationship details
        "description": """Analyze the provided character sheets and determine the relationship between the two NPCs.
                            Please provide the following details:
                            1. Relationship Type: The nature of the relationship between the two NPCs.
                            2. Relationship Dynamic: The power dynamic or balance in the relationship.
                            3. Relationship Strength: The intensity or depth of the relationship.
                            4. Relationship Keywords: 2-3 keywords that best describe the relationship.""",  # Description of the function template
        "parameters": {  # Parameters of the function template
            "type": "object",  # Type of the parameters (object)
            "properties": {  # Properties of the parameters
                "relationship_type": {  # Property for the relationship type
                    "type": "string",  # Type of the relationship_type property (string)
                    "description": "The nature of the relationship between the two NPCs.",  # Description of the relationship_type property
                    "enum": ["familial", "romantic", "platonic", "professional", "adversarial", "indifferent"]  # Enumerated values for the relationship_type property
                },
                "relationship_dynamic": {  # Property for the relationship dynamic
                    "type": "string",  # Type of the relationship_dynamic property (string)
                    "description": "The power dynamic or balance in the relationship.",  # Description of the relationship_dynamic property
                    "enum": ["equal", "leader-follower", "mentor-mentee", "rivals", "dependent-supporter", "exploitative"]  # Enumerated values for the relationship_dynamic property
                },
                "relationship_strength": {  # Property for the relationship strength
                    "type": "string",  # Type of the relationship_strength property (string)
                    "description": "The intensity or depth of the relationship.",  # Description of the relationship_strength property
                    "enum": ["strong", "moderate", "weak", "volatile", "distant", "unknown"]  # Enumerated values for the relationship_strength property
                },
                "relationship_keywords": {  # Property for the relationship keywords
                    "type": "array",  # Type of the relationship_keywords property (array)
                    "description": "2-3 keywords that best describe the relationship.",  # Description of the relationship_keywords property
                    "items": {  # Items within the relationship_keywords array
                        "type": "string"  # Type of each item in the relationship_keywords array (string)
                    },
                    "minItems": 1,  # Minimum number of items in the relationship_keywords array
                    "maxItems": 3  # Maximum number of items in the relationship_keywords array
                },
                "tldr": {  # Property for the relationship TLDR
                    "type": "string",  # Type of the tldr property (string)
                    "description": "Describe in one sentence and less than 5 words how the tldr works. This should be like mother, follows me, i'm the leader, part of friend group, student in class, etc."  # Description of the tldr property
                }
            },
            "required": ["relationship_type", "relationship_dynamic", "relationship_strength", "relationship_keywords", "tldr"]  # Required properties for the relationship details
        }
    }
]

class NPC:
    def __init__(self, game_details, persona, occupation, motivating_factor, api_key, names=None):
        """
        Initialize an NPC object with the provided game details, persona, occupation, motivating factor, API key, and optional names.

        Args:
            game_details (dict): A dictionary containing the game details (setting, mood, feelings, storyboard).
            persona (str): The persona of the NPC.
            occupation (str): The occupation of the NPC.
            motivating_factor (dict): A dictionary containing the motivating factor details (name, description).
            api_key (str): The API key for accessing the OpenAI API.
            names (list, optional): A list of names of already defined NPCs. Defaults to None.
        """
        self.api_key = api_key  # Store the API key
        self.game_details = game_details  # Store the game details
        self.persona = persona  # Store the NPC's persona
        self.occupation = occupation  # Store the NPC's occupation
        self.motivating_factor = motivating_factor  # Store the NPC's motivating factor
        self.memory = []  # Initialize an empty list to store the NPC's memory
        self.relations = {}  # Initialize an empty dictionary to store the NPC's relationships

        # Generate character sheet, name, and other properties
        if names is None:
            character_details = self.generate_character_details()  # Generate character details without considering other NPC names
        else:
            character_details = self.generate_character_details(names)  # Generate character details considering other NPC names
        self.name = character_details['name']  # Store the NPC's name
        self.tldr = character_details['TLDR']  # Store the NPC's TLDR
        self.speech_pattern = character_details['speech_pattern']  # Store the NPC's speech pattern
        self.motivation = character_details['character_motivation']  # Store the NPC's motivation
        self.character_sheet = {  # Store the NPC's character sheet
            "intellect": character_details["intellect"],
            "charisma": character_details["charisma"],
            "integrity": character_details["integrity"],
            "resilience": character_details["resilience"],
            "kindness": character_details["kindness"]
        }

    def generate_character_details(self, other_names=None):
        """
        Generate character details for the NPC using the OpenAI API.

        Args:
            other_names (list, optional): A list of names of already defined NPCs. Defaults to None.

        Returns:
            dict: A dictionary containing the generated character details.
        """
        if other_names is None:
            messages = [
                {"role": "system", "content": "Generate character details for an NPC based on the provided persona, occupation, and motivating factor."},  # System message to set the context for the API request
                {"role": "user", "content": f"""The game is about: 
                                            Game setting description: {self.game_details['setting']}
                                            Game mood: {self.game_details['mood']}
                                            Desired feelings: {self.game_details['feelings']}
                                            Additional notes: {self.game_details['storyboard']}

                                            This NPC within the game needs to be about:
                                            Persona: {self.persona}
                                            Occupation: {self.occupation}
                                            Motivating Factor: {self.motivating_factor['motivating_name']} - {self.motivating_factor['motivating_description']}

                                            Find a name starting with {str(np.random.choice([i for i in "abcdefghijklmnopqrstuvwxyz"]))}
                                            """}  # User message containing the game details, NPC characteristics, and a random starting letter for the name
            ]
        else:
            messages = [
                {"role": "system", "content": "Generate character details for an NPC based on the provided persona, occupation, and motivating factor."},  # System message to set the context for the API request
                {"role": "user", "content": f"""The game is about: 
                                            Game setting description: {self.game_details['setting']}
                                            Game mood: {self.game_details['mood']}
                                            Desired feelings: {self.game_details['feelings']}
                                            Additional notes: {self.game_details['storyboard']}

                                            This NPC within the game needs to be about:
                                            Persona: {self.persona}
                                            Occupation: {self.occupation}
                                            Motivating Factor: {self.motivating_factor['motivating_name']} - {self.motivating_factor['motivating_description']}

                                            Some names of already defined npcs include: {other_names} (either find unique names or only if occupationally/characteristically interesting then make a relation of some sort. Most of the times do not do something like this and instead make an indepedent new character.)
                                            Find a name starting with {str(np.random.choice([i for i in "abcdefghijklmnopqrstuvwxyz"]))}
                                            """}  # User message containing the game details, NPC characteristics, names of other NPCs, and a random starting letter for the name
            ]
        client = OpenAI(api_key=self.api_key)  # Create an OpenAI client instance with the provided API key
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Specify the GPT-3.5 model to use
            messages=messages,  # Pass the messages list to the API
            temperature=0.7,  # Set the temperature for generating diverse character details
            functions=function_templates,  # Pass the function templates to the API
            function_call={"name": "npc_character_sheet"},  # Specify the function to call (npc_character_sheet)
        )  # Call the OpenAI API to generate character details
        json_string = response.choices[0].message.function_call.arguments  # Extract the function call arguments from the API response
        dictionary = json.loads(json_string)  # Parse the JSON string into a dictionary
        return dictionary  # Return the dictionary containing the generated character details

    def add_to_memory(self, conversation):
        """
        Add a conversation to the NPC's memory.

        Args:
            conversation (list): A list of conversation messages.
        """
        self.memory.extend(conversation)  # Extend the NPC's memory with the conversation messages
        if len(self.memory) > 8:  # If the memory exceeds 8 messages
            self.batch_summarize()  # Perform batch summarization of the memory

    def batch_summarize(self):
        """
        Summarize the NPC's conversation history using the OpenAI API.
        """
        messages = [
            {"role": "system", "content": "Summarize the provided conversation history into a concise summary."},  # System message to set the context for the API request
            {"role": "user", "content": f"Conversation history:\n{chr(10).join(self.memory)}\nPlease provide a concise summary of the conversation history."}  # User message containing the conversation history
        ]
        client = OpenAI(api_key=self.api_key)  # Create an OpenAI client instance with the provided API key
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Specify the GPT-3.5 model to use
            messages=messages,  # Pass the messages list to the API
            temperature=0  # Set the temperature to 0 for deterministic output
        )  # Call the OpenAI API to generate a summary of the conversation history
        summary = response.choices[0].message.content  # Extract the generated summary from the API response
        self.memory = [summary]  # Update the NPC's memory with the summary

    def set_relation(self, other_npc, extra_context=None):
        """
        Set the relationship between the NPC and another NPC using the OpenAI API.

        Args:
            other_npc (NPC): The other NPC object.
            extra_context (str, optional): Extra context for the relationship. Defaults to None.
        """
        if extra_context is None:
            messages = [
                {"role": "system", "content": "Analyze the provided character sheets and determine the relationship between the two NPCs."},
                {"role": "user", "content": f"""NPC 1:
                                            Name: {self.name}
                                            TLDR: {self.tldr}
                                            Speech Pattern: {self.speech_pattern}
                                            Motivation: {self.motivation}
                                            Character Sheet: {json.dumps(self.character_sheet)}

                                            NPC 2:
                                            Name: {other_npc.name}
                                            TLDR: {other_npc.tldr}
                                            Speech Pattern: {other_npc.speech_pattern}
                                            Motivation: {other_npc.motivation}
                                            Character Sheet: {json.dumps(other_npc.character_sheet)}
                                            
                                        Based on the provided information, please determine the relationship between the two NPCs from NPC 1 - i.e. {self.name}'s perspective.
            """}  # User message containing the character sheets of the two NPCs
        ]
        else:
            messages = [
                {"role": "system", "content": "Analyze the provided character sheets and determine the relationship between the two NPCs."},  # System message to set the context for the API request
                {"role": "user", "content": f"""NPC 1:
                                        Name: {self.name}
                                        TLDR: {self.tldr}
                                        Speech Pattern: {self.speech_pattern}
                                        Motivation: {self.motivation}
                                        Character Sheet: {json.dumps(self.character_sheet)}
                                        
                                        NPC 2:
                                        Name: {other_npc.name}
                                        TLDR: {other_npc.tldr}
                                        Speech Pattern: {other_npc.speech_pattern}
                                        Motivation: {other_npc.motivation}
                                        Character Sheet: {json.dumps(other_npc.character_sheet)}

                                        Context of relationship from their perspective:

                                        {extra_context}
                                        
                                        Based on the provided information, please determine the relationship between the two NPCs from NPC 1 - i.e. {self.name}'s perspective.
            """}  # User message containing the character sheets of the two NPCs and extra context for the relationship
            ]
        client = OpenAI(api_key=self.api_key)  # Create an OpenAI client instance with the provided API key
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Specify the GPT-3.5 model to use
            messages=messages,  # Pass the messages list to the API
            temperature=0.7,  # Set the temperature for generating diverse relationship details
            functions=function_templates,  # Pass the function templates to the API
            function_call={"name": "npc_relationship_sheet"},  # Specify the function to call (npc_relationship_sheet)
        )  # Call the OpenAI API to determine the relationship between the two NPCs
        json_string = response.choices[0].message.function_call.arguments  # Extract the function call arguments from the API response
        dictionary = json.loads(json_string)  # Parse the JSON string into a dictionary
        self.relations[other_npc.name] = dictionary  # Store the relationship dictionary in the NPC's relations dictionary with the other NPC's name as the key

    def export_npc(self, output_directory):
        """
        Export the NPC data to a JSON file in the specified output directory.

        Args:
            output_directory (str): The directory where the NPC JSON file will be saved.
        """
        if not os.path.exists(output_directory):  # If the output directory doesn't exist
            os.makedirs(output_directory)  # Create the output directory
        npc_data = {
            "name": self.name,
            "tldr": self.tldr,
            "speech_pattern": self.speech_pattern,
            "motivation": self.motivation,
            "character_sheet": self.character_sheet,
            "relations": self.relations
        }  # Create a dictionary containing the NPC data
        file_path = os.path.join(output_directory, f"{re.sub('[^a-zA-Z]', '_', self.name)}.json")  # Generate the file path for the NPC JSON file
        with open(file_path, "w") as file:  # Open the file in write mode
            json.dump(npc_data, file, indent=4)  # Write the NPC data to the JSON file with indentation for readability