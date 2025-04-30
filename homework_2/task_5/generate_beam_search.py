import logging
import time
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
from aim import Run, Text

MODEL_NAME       = 'Qwen/Qwen2.5-0.5B-Instruct'
EOS_TOKEN_ID     = 151645
MAX_NEW_TOKENS   = 1000
BEAM_SETTINGS    = [
    {'num_beams': 1,  'length_penalty': 1.0},
    {'num_beams': 4,  'length_penalty': 1.0},
    {'num_beams': 4,  'length_penalty': 0.5},
    {'num_beams': 4,  'length_penalty': 2.0},
    {'num_beams': 8,  'length_penalty': 1.0},
]

PROMPT_STORY = (
    '<|im_start|>system\n'
    'You are a storyteller. Generate a story based on user message.<|im_end|>\n'
    '<|im_start|>user\n'
    'Generate me a short story about a tiny hedgehog named Sonic.<|im_end|>\n'
    '<|im_start|>assistant\n'
)
PROMPT_JSON = (
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class BeamCandidate:
    def __init__(self, ids, logprob):
        self.ids = ids
        self.logprob = logprob

def beam_search(
    model, tokenizer,
    prompt: str,
    num_beams: int,
    length_penalty: float,
    eos_token_id: int,
    max_new_tokens: int
) -> str:
    encoding = tokenizer(prompt, return_tensors='pt')
    device = model.device
    input_ids = encoding.input_ids.to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=torch.ones_like(input_ids))
        next_logits = outputs.logits[0, -1]
        next_logprobs = F.log_softmax(next_logits, dim=-1)
    topk_logprobs, topk_indices = torch.topk(next_logprobs, num_beams)

    incomplete = [
        BeamCandidate(
            ids=torch.cat([input_ids[0], idx.unsqueeze(0)]).unsqueeze(0),
            logprob=lp.item()
        )
        for lp, idx in zip(topk_logprobs, topk_indices)
    ]
    complete = []

    start_time = time.time()

    for step in range(max_new_tokens - 1):
        all_candidates = []

        for cand in incomplete:
            if cand.ids[0, -1].item() == eos_token_id:
                complete.append(cand)
                continue
            with torch.no_grad():
                out = model(
                    input_ids=cand.ids,
                    attention_mask=torch.ones_like(cand.ids)
                )
                logits = out.logits[0, -1]
                logprobs = F.log_softmax(logits, dim=-1)
            topk_lp, topk_idx = torch.topk(logprobs, num_beams)
            for lp, idx in zip(topk_lp, topk_idx):
                new_ids = torch.cat([cand.ids, idx.unsqueeze(0).unsqueeze(0)], dim=1)
                all_candidates.append(
                    BeamCandidate(
                        ids=new_ids,
                        logprob=cand.logprob + lp.item()
                    )
                )

        all_candidates.sort(key=lambda c: c.logprob, reverse=True)

        incomplete = []
        for c in all_candidates:
            if len(incomplete) >= num_beams:
                break
            if c.ids[0, -1].item() == eos_token_id:
                complete.append(c)
            else:
                incomplete.append(c)

        if len(complete) >= num_beams:
            break


    if not complete:
        complete = incomplete

    def score(c):
        length = c.ids.shape[1] ** length_penalty
        return c.logprob / length
    best = max(complete, key=score)

    elapsed = time.time() - start_time
    num_generated = best.ids.shape[1] - input_ids.shape[1]
    logger.info(
        "Генерация завершена: %d токенов за %.2f сек.", num_generated, elapsed
    )

    return tokenizer.decode(best.ids[0].tolist(), skip_special_tokens=True)

if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    run = Run(experiment='beam_search_generation')
    logger.info("Loading model %s", MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(device).eval()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    for params in BEAM_SETTINGS:
        nb = params['num_beams']
        lp = params['length_penalty']
        logger.info(f"Running beam search: num_beams={nb}, length_penalty={lp}")

        story = beam_search(
            model, tokenizer,
            prompt=PROMPT_STORY,
            num_beams=nb,
            length_penalty=lp,
            eos_token_id=EOS_TOKEN_ID,
            max_new_tokens=MAX_NEW_TOKENS
        )
        print(f"\n=== Hedgehog story (beams={nb}, lp={lp}) ===\n{story}\n")

        js = beam_search(
            model, tokenizer,
            prompt=PROMPT_JSON,
            num_beams=nb,
            length_penalty=lp,
            eos_token_id=EOS_TOKEN_ID,
            max_new_tokens=MAX_NEW_TOKENS
        )
        print(f"=== JSON (beams={nb}, lp={lp}) ===\n{js}\n")

        run.track(Text(story), name='story', context={'num_beams': nb, 'length_penalty': lp})
        run.track(Text(js),    name='json',  context={'num_beams': nb, 'length_penalty': lp})