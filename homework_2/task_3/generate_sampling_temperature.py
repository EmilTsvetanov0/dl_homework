import logging
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from aim import Run

MODEL_NAME = 'Qwen/Qwen2.5-0.5B-Instruct'
EOS_TOKEN_ID = 151645
MAX_NEW_TOKENS = 1000
TEMPERATURES = [0.001, 0.1, 0.5, 1.0, 10.0]

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

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

def sampling_decode_temp(model, tokenizer, prompt: str, eos_token_id: int, max_new_tokens: int, temperature: float) -> str:
    encoding = tokenizer(prompt, return_tensors='pt')
    input_ids = encoding.input_ids
    device = model.device
    input_ids = input_ids.to(device)

    generated_ids = input_ids
    logger.info("Начало генерации. Длина контекста: %d токенов", generated_ids.shape[1])
    start_time = time.time()

    for step in range(max_new_tokens):
        attention_mask = torch.ones_like(generated_ids, device=device)
        with torch.no_grad():
            outputs = model(input_ids=generated_ids, attention_mask=attention_mask)
        logits = outputs.logits
        next_token_logits = logits[0, -1] / temperature

        next_token_id = torch.multinomial(torch.softmax(next_token_logits, dim=-1), 1).unsqueeze(0)

        generated_ids = torch.cat([generated_ids, next_token_id], dim=1)

        token_id = next_token_id.item()
        logger.debug("Шаг %d: сгенерирован токен %d", step+1, token_id)

        if token_id == eos_token_id:
            logger.info("EOS-токен (ID=%d) сгенерирован на шаге %d.", eos_token_id, step+1)
            break

    elapsed = time.time() - start_time
    num_generated = generated_ids.shape[1] - input_ids.shape[1]
    logger.info(
        "Генерация завершена: %d токенов за %.2f сек.", num_generated, elapsed
    )

    run.track(num_generated, name='num_generated_tokens', context={'prompt': prompt[:30], 'temperature': temperature})
    run.track(elapsed, name='generation_time', context={'prompt': prompt[:30], 'temperature': temperature})

    output_text = tokenizer.decode(generated_ids[0].tolist(), skip_special_tokens=True)

    del generated_ids
    torch.cuda.empty_cache()


    return output_text

if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # device = torch.device('cpu')

    run = Run(experiment='sampling_generation_with_temperature')

    logger.info("Загружаем модель %s ...", MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(device).eval()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    for temp in TEMPERATURES:
        logger.info("Запуск генерации с температурой: %.3f", temp)
        story = sampling_decode_temp(
            model, tokenizer,
            prompt=input_text_hedgehog,
            eos_token_id=EOS_TOKEN_ID,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=temp
        )
        print(f"\n=== Generated hedgehog story (Temperature {temp}) ===\n")
        print(story)

    for temp in TEMPERATURES:
        logger.info("Запуск генерации с температурой: %.3f", temp)
        json_output = sampling_decode_temp(
            model, tokenizer,
            prompt=input_text_json,
            eos_token_id=EOS_TOKEN_ID,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=temp
        )
        print(f"\n=== Generated JSON (Temperature {temp}) ===\n")
        print(json_output)
