import streamlit as st  # Import the Streamlit library for building the web app
from openai import OpenAI  # Import the OpenAI library for accessing the GPT-3 API
import json  # Import the json library for parsing JSON data
import numpy as np  # Import the numpy library for numerical operations
from npc import NPC  # Import the NPC class from the npc module

# Read the secret key from the ".secrets" file
with open(".secrets", "r") as f:
    secret_key = f.read()  # Read the contents of the file and store it in the secret_key variable

downscale_factor = 1  # Set the downscale factor to 1 (used for scaling the number of characteristics, occupations, and motivating entities)

def create_custom_function_template(num_personas, num_occupations, num_motivating_entities):
    """
    Create a custom function template for generating NPC characteristics.

    Args:
        num_personas (int): The number of personas to generate.
        num_occupations (int): The number of occupations to generate.
        num_motivating_entities (int): The number of motivating entities to generate.

    Returns:
        list: A list containing the function template for generating NPC characteristics.
    """
    function_templates = [
        {
            "name": "npc_world_builder",  # Name of the function template
            "description": """Generate unique lists of personas, occupations, and motivations for NPCs based on the game's setting, mood, feelings, and additional notes. Ensure each individual keyword within the group is unique it each other can be universally mixed-and-match across the different lists. I.e, the individual personas can be combined across occupations, etc.

            Objectives:
            Create {num_personas} number of personas, each diverse in their own right
            Create {num_occupations} number of occupations, each diverse yet realistically important to the world/story
            Create {num_motivating_entities} number of occupations, each diverse yet makes sense from thematic perspective in this world.
            """,  # Description of the function template
            "parameters": {  # Parameters of the function template
                "type": "object",  # Type of the parameters (object)
                "properties": {  # Properties of the parameters
                    "personas": {  # Property for personas
                        "type": "array",  # Type of the personas property (array)
                        "items": {  # Items within the personas array
                            "type": "string",  # Type of each item in the personas array (string)
                            "description": "List of unique/diverse personas which can be characteristics/archetypes/etc. Example: Anything from stutter to confused to excited to anything & everything."  # Description of the personas property
                        }
                    },
                    "occupations": {  # Property for occupations
                        "type": "array",  # Type of the occupations property (array)
                        "items": {  # Items within the occupations array
                            "type": "string",  # Type of each item in the occupations array (string)
                            "description": "List of unique/diverse occupations which would be availale within the defined world. Example: Anything from fishing to cyberpunk gizmo."  # Description of the occupations property
                        }
                    },
                    "motivating_entities": {  # Property for motivating entities
                        "type": "array",  # Type of the motivating_entities property (array)
                        "items": {  # Items within the motivating_entities array
                            "type": "object",  # Type of each item in the motivating_entities array (object)
                            "description": "List of unique/diverse motivating_entities which would exist within world, like gods, religious groups, political parties, think hard, name them based on inter-relations if required",  # Description of the motivating_entities property
                            "properties": {  # Properties of each motivating entity object
                                "motivating_name": {  # Property for the name of the motivating entity
                                    "type": "string",  # Type of the motivating_name property (string)
                                    "description": "name of motivating entity"  # Description of the motivating_name property
                                },
                                "motivating_description": {  # Property for the description of the motivating entity
                                    "type": "string",  # Type of the motivating_description property (string)
                                    "description": "TLDR the description in one sentence. Not more than 11 words."  # Description of the motivating_description property
                                }
                            },
                            "required": ["name", "description"]  # Required properties for each motivating entity object
                        }
                    },
                },
                "required": ["personas", "occupations", "motivating_entities"]  # Required properties for the parameters object
            }
        }
    ]
    return function_templates  # Return the function templates list

def generate_lists(api_key, game_details):
    """
    Call the OpenAI API to generate lists of personas, occupations, and motivations based on the provided game details.

    Args:
        api_key (str): The API key for accessing the OpenAI API.
        game_details (dict): A dictionary containing the game details (setting, mood, feelings, storyboard).

    Returns:
        dict: A dictionary containing the generated lists of personas, occupations, and motivating entities.
    """
    messages = [
        {"role": "system", "content": "Generate lists of unique personas, occupations, and motivations for a game."},  # System message to set the context for the API request
        {"role": "user", "content": f"""Game setting description: {game_details['setting']}
                                        Game mood: {game_details['mood']}
                                        Desired feelings: {game_details['feelings']}
                                        Additional notes: {game_details['storyboard']}
                                        Please provide diverse and unique lists for personas, occupations, and motivations based on these inputs."""}  # User message containing the game details
    ]
    client = OpenAI(api_key=api_key)  # Create an OpenAI client instance with the provided API key
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",  # Specify the GPT-3.5 model to use
        messages=messages,  # Pass the messages list to the API
        temperature=0,  # Set the temperature to 0 for deterministic output
        functions=game_details['function_templates'],  # Pass the function templates to the API
        function_call={"name": "npc_world_builder"},  # Specify the function to call (npc_world_builder)
    )  # Call the OpenAI API to generate the lists
    json_string = response.choices[0].message.function_call.arguments  # Extract the function call arguments from the API response
    dictionary = json.loads(json_string)  # Parse the JSON string into a dictionary
    if len(dictionary["personas"]) > game_details['num_characteristics']:  # If the number of generated personas exceeds the desired number of characteristics
        dictionary["personas"] = np.random.choice(dictionary["personas"], replace=False, size=game_details['num_characteristics']).tolist()  # Randomly select a subset of personas
    if len(dictionary["occupations"]) > game_details['num_occupations']:  # If the number of generated occupations exceeds the desired number of occupations
        dictionary["occupations"] = np.random.choice(dictionary["occupations"], replace=False, size=game_details['num_occupations']).tolist()  # Randomly select a subset of occupations
    if len(dictionary["motivating_entities"]) > game_details['num_motivating_entities']:  # If the number of generated motivating entities exceeds the desired number of motivating entities
        indices = np.random.choice(np.arange(len(dictionary["motivating_entities"])), replace=False, size=game_details['num_motivating_entities'])  # Randomly select indices for a subset of motivating entities
        dictionary["motivating_entities"] = [dictionary["motivating_entities"][i] for i in indices]  # Select the motivating entities based on the randomly selected indices
    return dictionary  # Return the dictionary containing the generated lists

def app():
    """
    The main Streamlit app function for configuring and generating NPCs.
    """
    st.title("NPC Generator Configuration")  # Set the title of the Streamlit app

    with st.form("game_info"):  # Create a form for game details
        setting = st.text_input("Enter the game setting (e.g., medieval, futuristic)")  # Text input for the game setting
        mood = st.text_input("What mood do you want for the game? (e.g., dark, whimsical)")  # Text input for the game mood
        feelings = st.text_input("What feelings should the game evoke? (e.g., fear, excitement)")  # Text input for the desired feelings
        storyboard = st.text_input("Any additional notes or storyboard details?")  # Text input for additional notes or storyboard details

        col1, col2 = st.columns(2)  # Create two columns for sliders
        with col1:
            npc_diversity = st.slider("Diversity of Occupations", 0.0, 1.0, 0.5)  # Slider for the diversity of occupations
        with col2:
            num_npcs = st.slider("Number of NPCs", 1, 20, 8)  # Slider for the number of NPCs to generate
        col3, col4 = st.columns(2)  # Create two more columns for sliders
        with col3:
            motivation_diversity = st.slider("Diversity of Motivations", 0.0, 1.0, 0.5)  # Slider for the diversity of motivations
        with col4:
            character_diversity = st.slider("Diversity of Character Traits", 0.0, 1.0, 0.5)  # Slider for the diversity of character traits
        
        submitted = st.form_submit_button("Generate NPC Characteristics")  # Submit button to generate NPC characteristics
        if submitted:  # If the form is submitted
            game_details = {
                'setting': setting,  # Store the game setting in the game_details dictionary
                'mood': mood,  # Store the game mood in the game_details dictionary
                'feelings': feelings,  # Store the desired feelings in the game_details dictionary
                'storyboard': storyboard,  # Store the storyboard details in the game_details dictionary
                'num_occupations': int(num_npcs * character_diversity / downscale_factor),  # Calculate the number of occupations based on the number of NPCs, character diversity, and downscale factor
                'num_characteristics': int(num_npcs * npc_diversity / downscale_factor),  # Calculate the number of characteristics based on the number of NPCs, NPC diversity, and downscale factor
                'num_motivating_entities': int(num_npcs * motivation_diversity / downscale_factor),  # Calculate the number of motivating entities based on the number of NPCs, motivation diversity, and downscale factor
                'function_templates': create_custom_function_template(int(num_npcs * character_diversity / downscale_factor), int(num_npcs * npc_diversity / downscale_factor), int(num_npcs * motivation_diversity / downscale_factor))  # Create custom function templates based on the calculated values
            }
            api_key = secret_key  # Set the API key to the secret key
            result = generate_lists(api_key, game_details)  # Generate lists of personas, occupations, and motivations using the OpenAI API
            name_list = []  # Initialize an empty list to store NPC names
            npc_nodes = []  # Initialize an empty list to store NPC nodes
            my_bar = st.progress(0.0, text="Generating characters")  # Create a progress bar for character generation
            for character_i in range(num_npcs):  # Loop through the number of NPCs to generate
                selected_persona = np.random.choice(result["personas"])  # Randomly select a persona from the generated personas list
                selected_occupation = np.random.choice(result["occupations"])  # Randomly select an occupation from the generated occupations list
                selected_motivation = result["motivating_entities"][int(np.random.choice(np.arange(len(result["motivating_entities"]))))]  # Randomly select a motivating entity from the generated motivating entities list
                if len(name_list) == 0:  # If the name list is empty (first NPC)
                    npc_node = NPC(game_details, selected_persona, selected_occupation, selected_motivation, api_key)  # Create an NPC node without a name list
                else:  # If the name list is not empty (subsequent NPCs)
                    npc_node = NPC(game_details, selected_persona, selected_occupation, selected_motivation, api_key, name_list)  # Create an NPC node with the name list
                st.write(npc_node.name, npc_node.tldr, npc_node.character_sheet)  # Display the NPC name, TLDR, and character sheet in the Streamlit app
                name_list.append(npc_node.name)  # Add the NPC name to the name list
                npc_nodes.append(npc_node)  # Add the NPC node to the npc_nodes list
                for npc_node_idx in range(len(npc_nodes) - 1):  # Loop through the previously generated NPC nodes
                    npc_node.set_relation(npc_nodes[npc_node_idx])  # Set the relationship between the current NPC and the previous NPC
                    npc_nodes[npc_node_idx].set_relation(npc_node, json.dumps(npc_node.relations))  # Set the relationship between the previous NPC and the current NPC
                my_bar.progress((character_i + 1) / num_npcs, text="Generating character: " + npc_node.name)  # Update the progress bar with the current character generation progress

            for character_i in range(num_npcs):  # Loop through the generated NPCs
                node = npc_nodes[character_i].export_npc("./characters")  # Export the NPC data to the "./characters" directory

if __name__ == "__main__":
    app()  # Run the Streamlit app