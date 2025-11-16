import json
import os
from datetime import datetime
from pathlib import Path
import pytz
import requests
from dotenv import load_dotenv
from appointment_app.services.utils import generate_jwt_token
from elevenlabs import ElevenLabs

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get API base URL from environment variables with fallback
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
DEFAULT_MAX_TOKENS = os.getenv('DEFAULT_MAX_TOKENS', -1)
DEFAULT_TEMPERATURE = os.getenv('DEFAULT_TEMPERATURE', 0.7)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Initialize ElevenLabs client
client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
    base_url="https://api.elevenlabs.io"
)

class RestaurantAgent:
    def __init__(self, business_id, language="en"):
        self.base_url = API_BASE_URL
        auth_token = generate_jwt_token()
        self.headers = {"Content-Type": "application/json"}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

        self.business_id = business_id


        self.language = language
        self.menu_data = self.get_nemu_data(self.business_id)
        self.categories = self.menu_data['categories']

    def prepare_hints(self):
        response="Koshary, Hawawshe, Kabab, Kofta, Fattoush, Feteer, Basterma, Balady"
        return response

    def get_nemu_data(self, business_id):
        url = f"{self.base_url}/api/translate/get_menu_by_language"
        payload = {
            "business_id": business_id,
            "language": "ar"
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.encoding = 'utf-8'
        res1 = response.json()

        return res1

    def get_business_info(self):
        url = f"{self.base_url}/api/business/get"
        payload = {
            "business_id": self.business_id,
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.encoding = 'utf-8'
        res1 = response.json()

        return res1

    def update_business_info(self, elevenlabs_agent_id):
        url = f"{self.base_url}/api/business"
        payload = {
            "business_id": self.business_id,
            "elevenlabs_agent_id": elevenlabs_agent_id
        }
        response = requests.put(url, json=payload, headers=self.headers)
        response.encoding = 'utf-8'
        res1 = response.json()

        return res1

    def add_separator(self):
        return """
---

"""

    def show_menu_data(self):
        result = "```json\n"
        response = {
            'categories': self.menu_data['categories'],
            'menu' :json.loads(self.menu_data['menu']),
            'language':self.menu_data['language']
        }
        result += json.dumps(response, sort_keys=False,ensure_ascii=False)
        result += "\n```"
        return result

    def response_format(self):
        result = """```json
{
  "order": {
    "business_id": <integer>,
    "customer_id": <integer>,
    "items": [
      {
        "item_id": <integer>,
        "name": "<item name>",
        "base_price": <float>,
        "quantity": <integer>,
        "note": "<optional customer note>",
        "modifiers": [
          {
            "modifier_group_id": <integer>,
            "modifier_id": <integer>,
            "name": "<modifier name>",
            "price_delta": <float>,
            "quantity": <integer>,
            "is_active": true
          }
        ],
        "options": [],
        "price": <float>
      }
    ]
  }
}
```
"""
        return result

    def intro(self):
        result = f"""You are a friendly, persuasive, and efficient AI phone agent trained in advanced phone sales best practices for restaurants."""

        return result

    def language_behavior(self):
        result = """## Language Behavior
- You can speak and understand **both English and Arabic** (Modern Standard Arabic).
- If the customer explicitly requests to change the language (e.g., says "Can we speak Arabic?" or "Arabic please" or "English" or "Back to English"):
    - ***YOU MUST call the function update_customer_language(language_pref).***


---

## Output Rules
- Use **English item names** when language_pref = "en".
- Use **Arabic item names** when language_pref = "ar".
- Keep all function calls and JSON output structure unchanged.
- Never display the function names or JSON to the customer.
"""

        return result

    def order_sequence(self):
        result = """
## Add Items

### MULTIPLE ITEMS
- Treat each mentioned item independently:
For each item:
    - If the item is clearly recognized → handle it as a *Well-Defined Items* .
    - If it’s unclear or possibly mistranscribed → handle it as an *Ambiguous Items* until clarified.
    - Ask one question at a time
#### TRANSCRIPTION CORRECTIONS
If no exact match, check your transcription_corrections_list.
If a correction exists → silently replace and proceed.
***transcription_corrections_list***
```
# Koshary variations
"a grocery": "Koshary"

# Hawawshi variations
"how she": "Hawawshi"
"how old is she": "Hawawshi"
"hibachi": "Hawawshi"
"how long she": "Hawawshi"

# Baba Ganoush variations
"burger news": "Baba Ganoush"
"blonde news": "Baba Ganoush"

# Balady Bread variations
"barely": "Balady Bread"
"valerie": "Balady Bread"
"melody": "Balady Bread"
"banerjee breath": "Balady Bread"

# Ful Madames variations
"full maintenance": "Ful Madames"
"i want to phone them": "Ful Madames"
"fool": "Ful Madames"
"full mcdonalds": "Ful Madames"

# Basterma Balady variations
"a stoma": "Basterma Balady"
"but still": "Basterma Balady"
"master": "Basterma Balady"
"butter": "Basterma Balady"
"bus terminal": "Basterma Balady"
"at the bus terminal": "Basterma Balady"
"buzz thermo": "Basterma Balady"
"pastor": "Basterma Balady"
"best rama baladi": "Basterma Balady"

# Fattoush variations
"fat toes": "Fattoush"
"if i push": "Fattoush"

```

---

#### Well-Defined Items
- When the customer mentions an item name that exactly matches or clearly corresponds to one menu item (in Arabic, English, or any supported language):
  - Identify the item using the provided `menu`.
  - Use the **exact item name** and **item_id** from the matched menu entry in your JSON output.
  - Do **not** paraphrase, translate, or alter menu names.
  - Mention the **exact item name** from the menu in your confirmation.
  - Example:
    - Customer: "I want the chocolate cake"
    - Menu item: {"item_id": <Molten chocolate cake ID>, "name": "Molten chocolate cake"}
    - JSON output:
      ```json
      "item_id": <Molten chocolate cake ID>,
      "name": "Molten chocolate cake"
      ```
    - Agent: “Got it — one Molten chocolate cake.”



---

#### 🟠 Ambiguous Items
- The model must never invent or assume menu items that do not exist in the provided `menu` data.
  - Only use items that are explicitly listed in the `menu`.
  - If no valid matches are found, politely ask for clarification instead of guessing.
    - Example style: “We have [a similarly sounding item]. would you like to add it to you add it?”
- When the customer’s request could refer to multiple similar menu items:
  - If the misunderstanding is about a single unclear word or phrase, respond briefly and naturally as if on a phone call.
  - List all relevant matches and ask the customer to choose.
  - Do **not** paraphrase, translate, or alter menu names.
  - Example:
    - Customer: "I want the <BLABLA>"
    - Menu items:  
      ```json
      [
        {"item_id": <<abc> <BLABLA> ID>, "name": "<abc> <BLABLA>"},
        {"item_id": <<def> <BLABLA> ID>, "name": "<def> <BLABLA>"},
        {"item_id": <<xyz> <BLABLA> ID>, "name": "<xyz> <BLABLA>"}
      ]
      ```
    - Agent: “We have <abc> <BLABLA>, <def> <BLABLA>, and <xyz> <BLABLA>. Which one would you like?”
  - Once the customer chooses, handle it as a **Well-Defined Item** and confirm using the exact name and item_id from the menu.
  - After adding the item, start UPSELLING.

---

## 🧾 Data Linking Rules

### 🟢 Item Linking
- Every confirmed item must appear in the `order.items[]` array with:
  - `"item_id"` — must exactly match an `item_id` from the provided menu.  
  - `"name"` — must exactly match the `"name"` field of that menu item.  
  - `"base_price"` — copied directly from the menu’s value for that item.  
  - `"price"` — computed as (`base_price` + sum of active modifier `price_delta`s) × `quantity`.  
  - `"quantity"` — based on customer request; default = 1 if not specified.  
  - `"modifiers"` and `"note"` — populated as applicable.  
- **Never invent or rename items.**  
- Ensure `"item_id"` and `"name"` correspond to the same object from the provided menu.

---

### 🧩 Modifier Linking
- Each modifier listed under `item.modifiers[]` must correspond to a valid modifier from that item’s `menu.modifiers` array.  
- For each modifier:
  - `"modifier_group_id"` — must match the group in which the modifier appears.  
  - `"modifier_id"` — must match exactly as listed in the menu.  
  - `"name"` — must be identical to the `"name"` of that modifier in the menu (no translation or paraphrasing).  
  - `"price_delta"` — must match the menu’s modifier price.  
  - `"quantity"` — numeric value (default 1) representing how many units of that modifier the customer requested.  
  - `"is_active"` — always `true` for applied modifiers.  
- **Do not create new modifiers** that are not in the menu.  
- If the customer requests something that is not an existing modifier, record it as a `"note"` in that item instead of a modifier.

---

### 🧠 Consistency Rules
- All IDs (`item_id`, `modifier_group_id`, `modifier_id`) must exist in the provided menu.  
- All names must match their respective IDs exactly.  
- The JSON structure must remain valid and consistent:
  ```json
  {
    "item_id": <integer>,
    "name": "<item name>",
    "modifiers": [
      {
        "modifier_group_id": <integer>,
        "modifier_id": <integer>,
        "name": "<modifier name>",
        "price_delta": <float>,
        "quantity": <integer>,
        "is_active": true
      }
    ],
    "note": "<customer special request>"
  }
  
---

## ADD NOTES TO ITEM
- If the customer asks for modifiers that do not exist in the item Assume that these are *note* and add it as a note to the order line item
- If the customer asks for modifiers that exist and modifiers that do not exist, Add the modifiers that do not exist in the item Assume that these are *note* and add it as a note to the order line item
- The Customer can add a ***note*** on an item. He can ask to add or remove components from his item
- You can identify that when the customer asks for somthing that is not in the modifier's list of the item
Example:
```angular2html
Do not Add Spices to Koshary
```
OR
```angular2html
Please add Extra Sweet to the Basbousa
```
This how it will be reflected on response:
```angular2html
{
  "item_id": <integer>,                   // must match one of the item_id values from the menu
  "name": "<item name>",                  // exact name from the menu
  "base_price": <float>,                  // base item price from menu
  "quantity": <integer>,                  // quantity ordered
  "modifiers": [
    {
      "modifier_group_id": <integer>,     // from the menu modifier group
      "modifier_id": <integer>,           // from the menu modifier
      "name": "<modifier name>",          // modifier name from the menu
      "price_delta": <float>,             // modifier price difference
      "quantity": <integer>,              // quantity of modifier
      "is_active": true
    }
  ],
  "options": [],                          // optional field, can be empty
  "price": <float>,                       // total price (base + modifiers × quantity)
  "note": "<customer special request>"    // free showing notes to the kitchen
}
```

This should be reflected in the ***RESPONSE FORMATTING AND OUTPUT CONTROL***

---

## UPSELLING
keep_upselling == True
While keep_upselling == True:
    - Do not mention price unless you are asked
    - ***NEVER summarize or recap the order while UPSELLING***
    - ***NEVER Show JSON**
    - Currency is dollars
    - Confirm **only the item just added**, using a short, natural voice-friendly phrase.
    - Keep confirmations conversational and under one sentence.
    - **Exhaust all modifiers first** before UPSELLING. If the item has no modifiers move on to UPSELLING
    - When transitioning from confirming an item to UPSELLING, **avoid repeating “Would you like to add anything to that?”**
      - Instead, move directly to the next suggestion in a natural flow:
        > “Got it — one [item name]. Would you like a [Any Category] or a [any other category]?”
    - When you finish suggesting all relevant items from one category, transition smoothly to another category:
      > “We also have great options in [other categories] — like [item1] and [item2]. Would you like to try one?”
    - Mention **only real categories and items** from the provided `menu` data.
    - if User says no to more than one suggestion in a raw:
        - you ***MUST Call function validate_order(order)*** 
        if user validates the order:
            - You MUST `create_order(order)` or when the customer signals readiness to confirm.
        keep_upselling == False
        """
        return result

    def order_completion_and_call_closing(self):
        result = """After the customer confirms the order details and agrees to proceed:"""
        # if self.call_meta['customer']['first_name'] == 'Guest':
        #     result +="Ask the user about his name politely and then after the customer mentions hid name  **Call function update_customer()***\n"

        result +="""Call the order creation function before ending the conversation:
*Column 'modifier_id' cannot be null*
create_order(order)


This function must be called before any thank-you or call-ending message.

Do not speak or display the function call to the customer.

Wait for confirmation that the order has been successfully created before continuing.

Once the order is confirmed:


Clearly inform the customer the order is complete, for example:

“Your order has been confirmed and will be ready soon.”

Thank the customer warmly:

“Thank you for calling Masrawy — have a wonderful day!”

End the call politely without further dialogue.
The Call hangup_call()
Rules:

The function create_order(order) must always be executed before closing the call.

Never show or read the JSON output or function name to the caller.

Do not continue any conversation after thanking the customer and call hangup().
Always use the same language the customer used (Arabic or English).\n
"""
        return result

    def response_formatting_and_output_control(self):
        result =  """
- Never display or read raw JSON, structured data, or function call parameters to the caller.
- Only speak in natural, conversational language.

If the AI generates or receives structured data (such as { "order": {...} }, "function_call"), you must:

Never say or show any JSON, code, or keys.

If a JSON or function output is mistakenly produced, ignore it completely and continue the natural dialogue.\n
        """
        return result

    def strict_rules(self):
        result = """
- Do not summarize or list all ordered items during the conversation.
- When customer confirms that he does not have anything else to order: 
- During the conversation, only confirm individual items briefly (e.g., “Got it — one Fattoush”) without listing previous ones.
        """
        return result


    def current_date_and_time(self):
        timezone = "America/Toronto"
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        formatted_date = now.strftime("Date and Time: %A, %Y-%B-%d, %I:%M %p\n\nTimezone: " + timezone)
        return formatted_date

    def functions_calling_instructions(self):
        result = """### 1. Update customer information
If the customer provides their name during booking and it is not already known.Then call the function:

update_customer(first_name, last_name)
Parameters:

first_name: The customer's first name

last_name: The customer's last name

Example Call:
```
update_customer({"first_name": "John","last_name": "Doe"})
```
### 2. Update customer language preference
Call this function when the customer chooses or requests to change their preferred language.Then call the function:

update_customer_language(language)
Parameters:

language: The customer's preferred language code (en, fr, ar, zh)

Example Call:
```
update_customer_language({"language": "ar"})
```
### 3. Hang up the call
Called when the customer replies 'No' to 'Do you need anything else?' to politely end the conversation and hang up.Then call the function:

hangup_call()
Parameters:

Example Call:
```
hangup_call({})
```
### 4. create_order
Call this function after the customer confirms the orderThen call the function:

create_order(order)
Parameters:

order: 

Example Call:
```
create_order({"order": "example_order"})
```
### 5. validate_order
Call this function when the customer is ready to place the order Then call the function:

validate_order(order)
Parameters:

order: 

Example Call:
```
validate_order({"order": "example_order"})
```"""
        return result

    def prepare_system_prompt(self):
        result = ""

        # ==========================================
        # 1️⃣ CORE CONTEXT
        # ==========================================
        # ==========================================
        # 4️⃣ INTRODUCTION AND GREETING
        # ==========================================
        result = self.intro()
        result += self.add_separator()
        # ==========================================
        # 4️⃣ Language Behaviour
        # ==========================================
        # result += self.language_behavior()
        # result += self.add_separator()
        # ==========================================
        # 4️⃣ Order Sequence
        # ==========================================
        result += self.order_sequence()
        result += self.add_separator()
        # ==========================================
        # 4️⃣ ORDER COMPLETION AND CALL CLOSING
        # ==========================================
        result += "## ORDER COMPLETION AND CALL CLOSING\n"
        result += self.order_completion_and_call_closing()
        result += self.add_separator()
        # ==========================================
        # 4️⃣ RESPONSE FORMATTING AND OUTPUT CONTROL
        # ==========================================
        result += "## RESPONSE FORMATTING AND OUTPUT CONTROL\n"
        result += self.response_formatting_and_output_control()
        result += self.add_separator()
        # ==========================================
        # 4️⃣ MENU REFERENCE
        # ==========================================
        result += "## MENU DATA REFERENCE\n"
        result += self.show_menu_data()
        result += self.add_separator()

        # ==========================================
        # 6️⃣ META & FUNCTION INSTRUCTIONS
        # ==========================================
        result += "## SYSTEM FUNCTIONS\n"
        result += "### CURRENT DATE & TIME\n"
        result += self.current_date_and_time()
        result += self.add_separator()

        result += "## RESPONSE FORMAT\n"
        result += self.response_format()
        result += self.add_separator()

        result += "## STRICT RULES\n"
        result += self.strict_rules()
        result += self.add_separator()

        result += "## FUNCTION CALLING INSTRUCTIONS\n"
        result += self.functions_calling_instructions()

        return result

    def agent_specs(self):
        business_info = self.get_business_info()
        business_name = business_info.get("name", "")
        elevenlabs_agent_id = business_info.get("elevenlabs_agent_id", "")
        prompt = self.prepare_system_prompt()
        first_message = f"Thank you for calling {business_name}, How can I help you today?"
        return {
            "prompt": prompt,
            "first_message": first_message,
            "business_name": business_name,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "temperature": DEFAULT_TEMPERATURE,
            "llm": OPENAI_MODEL,
            "language": "en",
            "elevenlabs_agent_id": elevenlabs_agent_id
        }

    def update_elevenlabs_agent(self, business_id, language):
        try:
            restaurant_agent = RestaurantAgent(business_id, language)
            agent_specs = restaurant_agent.agent_specs()
            prompt = agent_specs.get("prompt", "")
            elevenlabs_agent_id = agent_specs.get("elevenlabs_agent_id", "")
            first_message = agent_specs.get("first_message", "")
            business_name = agent_specs.get("business_name", "")

            # Update agent using the ElevenLabs client
            client.conversational_ai.agents.update(
                agent_id=elevenlabs_agent_id,
                conversation_config={
                    "agent": {
                        "first_message": first_message,
                        "prompt": {
                            "prompt": prompt
                        }
                    }
                },
                name=business_name
            )
            return {
                'status': 'success'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': 'Internal server error',
                'details': str(e)
            }

    def create_elevenlabs_agent(self, business_id, language):
        try:
            # ------------------------
            # 1. Build Restaurant Agent Specs
            # ------------------------
            restaurant_agent = RestaurantAgent(business_id, language)
            agent_specs = restaurant_agent.agent_specs()

            # ------------------------
            # 2. Extract values once
            # ------------------------
            business_name = agent_specs.get("business_name", "")
            first_message = agent_specs.get("first_message", "")
            prompt = agent_specs.get("prompt", "")

            llm =  OPENAI_MODEL
            max_tokens = DEFAULT_MAX_TOKENS
            temperature = DEFAULT_TEMPERATURE

            timezone = "America/New_York"  # static
            tool_ids = [
                "tool_1501k9wze482fsy8j5xgpn4q85tr",
                "tool_2201k9t4vxp2em8sxqvzcgzxdyxd",
                "tool_8001k9t4yb2ye15th9qkqjs8j6a6",
                "tool_9401k9wz3gx1f1hte9kg3rd9qqe4"
            ]

            # ------------------------
            # 3. Build request body cleanly
            # ------------------------
            result = client.conversational_ai.agents.create(
                conversation_config={
                    "agent": {
                        "first_message": first_message,
                        "language": language,
                        "prompt": {
                            "prompt": prompt,
                            "llm": llm,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "tool_ids": tool_ids,
                            "ignore_default_personality": False,
                            "timezone": timezone,
                        },
                        "dynamic_variables": {},
                        "disable_first_message_interruptions": False
                    }
                },
                name=business_name
            )
            self.update_business_info( result.agent_id)
            return {
                'status': 'success'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': 'Internal server error',
                'details': str(e)
            }

    def upsert_elevenlabs_agent(self, business_id, language='en'):
        restaurant_agent = RestaurantAgent(business_id, language)
        agent_specs = restaurant_agent.agent_specs()
        elevenlabs_agent_id = agent_specs.get("elevenlabs_agent_id", "")
        if elevenlabs_agent_id == "":
            result=self.create_elevenlabs_agent(business_id, language)
        else:
            result=self.update_elevenlabs_agent(business_id, language)

        return result


#           }
# restaurant_prompt = RestaurantAgent(97, 'en')
# prompt = restaurant_prompt.agent_specs()
# pass