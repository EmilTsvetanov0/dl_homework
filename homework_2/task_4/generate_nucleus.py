import logging
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from aim import Run, Text

MODEL_NAME = 'Qwen/Qwen2.5-0.5B-Instruct'
EOS_TOKEN_ID = 151645
MAX_NEW_TOKENS = 1000
PARAMS = [
    {'temperature': 1.0, 'top_p': 0.9},
    {'temperature': 1.0, 'top_p': 0.15},
    {'temperature': 0.5, 'top_p': 0.9},
    {'temperature': 0.5, 'top_p': 0.15},
]

# Промпты из условия
input_text_hedgehog = (
    '<|im_start|>system\n'
    'You are a storyteller. Generate a story based on user message.<|im_end|>\n'
    '<|im_start|>user\n'
    'Generate me a short story about a tiny hedgehog named Sonic.<|im_end|>\n'
    '<|im_start|>assistant\n'
)
input_text_json = (
    '<|im_start|>system\n'
    'You are a JSON machine. Generate a JSON with format '
    '{"contractor": string with normalized contractor name, '
    '"sum": decimal, '
    '"currency": string with uppercased 3-letter currency code} '
    'based on user message.<|im_end|>\n'
    '<|im_start|>user\n'
    'Transfer 100 rubles and 50 kopeck to Mike<|im_end|>\n'
    '<|im_start|>assistant\n'
)

# --- Logging setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

def nucleus_decode(model, tokenizer, prompt, eos_token_id, max_new_tokens, temperature, top_p):
    encoding = tokenizer(prompt, return_tensors='pt')
    input_ids = encoding.input_ids.to(model.device)
    generated_ids = input_ids

    start_time = time.time()

    for _ in range(max_new_tokens):
        attention_mask = torch.ones_like(generated_ids)
        with torch.no_grad():
            logits = model(input_ids=generated_ids, attention_mask=attention_mask).logits[0, -1] / temperature
        probs = torch.softmax(logits, dim=-1)

        sorted_probs, sorted_indices = torch.sort(probs, descending=True)
        cumulative = torch.cumsum(sorted_probs, dim=0)

        mask = cumulative <= top_p
        mask[0] = True
        filtered_probs = sorted_probs * mask
        filtered_probs = filtered_probs / filtered_probs.sum()

        choice_in_sorted = torch.multinomial(filtered_probs, num_samples=1)
        next_token_id = sorted_indices[choice_in_sorted].unsqueeze(0)

        generated_ids = torch.cat([generated_ids, next_token_id], dim=1)
        if next_token_id.item() == eos_token_id:
            break

    elapsed = time.time() - start_time
    num_generated = generated_ids.shape[1] - input_ids.shape[1]
    logger.info(
        "Генерация завершена: %d токенов за %.2f сек.", num_generated, elapsed
    )


    output_text = tokenizer.decode(generated_ids[0].tolist(), skip_special_tokens=True)

    del generated_ids
    torch.cuda.empty_cache()

    return output_text

if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    run = Run(experiment='nucleus_sampling')
    logger.info("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(device).eval()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    for params in PARAMS:
        t, p = params['temperature'], params['top_p']
        logger.info(f"Decoding with temperature={t}, top_p={p}")

        story = nucleus_decode(model, tokenizer, input_text_hedgehog,
                               EOS_TOKEN_ID, MAX_NEW_TOKENS, t, p)
        print(f"\n=== Hedgehog story (temp={t}, top_p={p}) ===\n{story}")

        js = nucleus_decode(model, tokenizer, input_text_json,
                            EOS_TOKEN_ID, MAX_NEW_TOKENS, t, p)
        print(f"\n=== JSON (temp={t}, top_p={p}) ===\n{js}\n")

        run.track(
            Text(story),
            name="story",
            context={"temperature": t, "top_p": p}
        )

        run.track(
            Text(js),
            name="json",
            context={"temperature": t, "top_p": p}
        )
