import argparse
import os
import sys
import torch
from download import write_line_by_line
from transformers import (
    AutoConfig, AutoModelWithLMHead, AutoTokenizer,
    DataCollatorForLanguageModeling, set_seed,
    TextDataset, Trainer, TrainingArguments)

# used in both finetune and generate_captions so make it global
tokenizer = AutoTokenizer.from_pretrained('gpt2')


def finetune(tag):
    """fine-tune gpt2 on the given caption dataset"""
    global tokenizer
    config = AutoConfig.from_pretrained('gpt2')
    model = AutoModelWithLMHead.from_pretrained('gpt2', config=config)
    block_size = tokenizer.max_len
    # https://github.com/huggingface/transformers/blob/448c467256332e4be8c122a159b482c1ef039b98/src/transformers/data/datasets/language_modeling.py
    try:
        train_dataset = TextDataset(
            tokenizer=tokenizer, file_path=f'./text/training_text/{tag}.txt',
            block_size=block_size, overwrite_cache=True)
        data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
        epochs = 8
        training_args = TrainingArguments(
            output_dir='logging/output',
            overwrite_output_dir=True,
            do_train=True,
            num_train_epochs=epochs,
            gradient_accumulation_steps=1,
            learning_rate=1e-4,
            per_gpu_train_batch_size=1,
            logging_steps=50,
            save_steps=0)
        set_seed(training_args.seed)
        trainer = Trainer(
            model=model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=train_dataset,
            prediction_loss_only=True)
        with open(f'./logging/training_stats/training_{tag}.log', 'w') as log:
            sys.stdout = log
            trainer.train()
        sys.stdout = sys.__stdout__
        # save the model
        if not os.path.exists(f'./trained_models/{tag}/'):
            os.makedirs(f'./trained_models/{tag}/')
        model.save_pretrained(f'./trained_models/{tag}/')
        print('Done!')
    except AssertionError:
        print(f'The training text with the tag = {tag} does not exist. No model was trained!')


# TODO: captions can always be cleaned/scored better
def generate_captions(tag, prompt, max_length, min_length, num_return_sequences):
    """generate captions from our fine-tuned model"""

    def clean_token(text):
        """edge case where the endoftext token can be left in generated"""
        token = '<|endoftext|>'
        while len(token)>1:
            text = text.replace(token, '')
            token = token[:-1]
        text = text.strip()
        if text[-1] == '"' and text.count('"') % 2: text = text[:-1]
        return text.strip()
    try:
        model = AutoModelWithLMHead.from_pretrained(f'./trained_models/{tag}/').to('cuda')
        encoded_sentence = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt").to('cuda')
        # https://huggingface.co/transformers/_modules/transformers/modeling_utils.html#PreTrainedModel.generate
        output_sequences = model.generate(
            input_ids= encoded_sentence,
            max_length=max_length,
            min_length=min_length,
            temperature=1.,
            top_p=0.95,
            do_sample=True,
            num_return_sequences=num_return_sequences)
        stop_token = '\n'
        generated_sequences = []
        for generated_sequence_idx, generated_sequence in enumerate(output_sequences):
            text = tokenizer.decode(generated_sequence, clean_up_tokenization_spaces=True)
            text = text[: text.find(stop_token)]
            # + 2 because it could be punctuation or emojis or both
            if len(text) > (len(prompt) + 2):
                generated_sequences.append(clean_token(text))
        # remove duplicates
        generated_sequences = list(set(generated_sequences))

        # just so I can see things better
        generated_text = '\nCAPTION: '.join(generated_sequences)
        generated_text = 'CAPTION: ' + generated_text
        write_line_by_line(f'./text/generated_text/{tag}_gen.txt', generated_text)
        print(f'Writing captions: /Hugging-Captions/text/generated_text/{tag}_gen.txt')
        print('Done!')
    except EnvironmentError:
        print(f'A model with the tag = {tag} does not exist. No captions were generated. Train a model first.')


def main():
    parser = argparse.ArgumentParser(
        description='Tune transformer model and generate captions'
        )
    parser.add_argument('--tag', type=str, help='Hashtag that we used to train the data', required=True)
    # finetune stuff (could add more params later)
    parser.add_argument('--train', action='store_true', default=False, help='Should we train the model (default: False)')
    # generate_caption stuff
    parser.add_argument('--generate', action='store_true', default=False, help='Should we generate captions')
    parser.add_argument('--prompt', type=str, default='My day',
        help='Give the model something to start with when generating text 1-5 words will due (default= My\ Day)')
    parser.add_argument('--max-length', type=int, default=60, help='Max length of caption text (default=60)')
    parser.add_argument('--min-length', type=int, default=20, help='Min length of caption text (default=20)')
    parser.add_argument('--num-captions', type=int, default=40,
        help='Number of captions to generate, some of these captions will be dropped because they are duplicates (default=40)')
    args = parser.parse_args()

    if (args.train and args.generate):
        print('Training and generating captions ...')
        finetune(args.tag)
        generate_captions(args.tag, args.prompt, args.max_length,
            args.min_length, args.num_captions)
    elif (args.train):
        print('Training ...')
        finetune(args.tag)
    elif (args.generate):
        print('Generating captions ...')
        generate_captions(args.tag, args.prompt, args.max_length,
            args.min_length, args.num_captions)
    else:
        print('Please choose either --train or --generate or both')


if __name__ == '__main__':
    main()
