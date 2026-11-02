#!/usr/bin/env python3
"""CPU-only verified FL2VA API-graph conversion; never submits a GPU request."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

LORA = 'minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors'
OLD_LORA = 'minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors'
BASE = 'minimax_h3_fl2va_pruned_int8_convrot.safetensors'
SIZE = 1956193000
SHA = 'c8168ebc17bbacc4296103dda2fec1ba85b24392fa08cf2bfbcef0cff0dc3cc8'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify_lora(path):
    path = Path(path)
    if path.stat().st_size != SIZE:
        raise ValueError('Incomplete or different LoRA: byte count mismatch')
    actual = digest(path)
    if actual != SHA:
        raise ValueError('Different LoRA: SHA256 mismatch')
    return {'sha256': actual, 'bytes': SIZE, 'recipe': 'FL2VA4_v1.2_video6_audio3'}


def convert(document, lora_name=LORA):
    result = copy.deepcopy(document)
    graph = result.get('prompt', result)
    if not isinstance(graph, dict) or not graph or any(
        not isinstance(v, dict) or 'class_type' not in v or not isinstance(v.get('inputs'), dict)
        for v in graph.values()
    ):
        raise ValueError('Expected ComfyUI API graph, not frontend workflow JSON')

    def one(kind):
        nodes = [k for k, n in graph.items() if n['class_type'] == kind]
        if len(nodes) != 1:
            raise ValueError('Expected one ' + kind)
        return nodes[0]

    if any(n['class_type'] == 'MiniMaxH3ReferenceToVideo' for n in graph.values()):
        raise ValueError('This FL2VA LoRA does not support Ref2VA')
    one('MiniMaxH3ImageToVideo')
    loaders = [n for n in graph.values() if 'unet_name' in n['inputs']]
    if len(loaders) != 1 or Path(loaders[0]['inputs']['unet_name']).name != BASE:
        raise ValueError('Unsupported or ambiguous base model')
    guider, scheduler, sampler = one('BasicGuider'), one('BasicScheduler'), one('KSamplerSelect')
    link = graph[guider]['inputs'].get('model')
    if link != graph[scheduler]['inputs'].get('model'):
        raise ValueError('Guider and scheduler must share the same MODEL')
    seen, replaced = set(), []
    while True:
        if not isinstance(link, list) or len(link) != 2 or link[1] != 0 or link[0] not in graph:
            raise ValueError('Invalid MODEL link')
        node_id = link[0]
        if node_id in seen:
            raise ValueError('Cyclic MODEL chain')
        seen.add(node_id)
        node = graph[node_id]
        if node['class_type'] == 'MiniMaxH3SigmaShift':
            pass
        elif node['class_type'] == 'LoraLoaderModelOnly':
            if node['inputs'].get('lora_name') not in (LORA, OLD_LORA):
                raise ValueError('Unknown existing LoRA; refusing to replace it')
        else:
            break
        replaced.append(node_id)
        link = node['inputs'].get('model')
    for node_id, node in graph.items():
        if 'LoraLoader' in node['class_type'] and node_id not in replaced:
            raise ValueError('Additional LoRA branch requires manual review')
        for value in node['inputs'].values():
            if (isinstance(value, list) and len(value) == 2 and value[0] in replaced
                    and node_id not in replaced + [guider, scheduler]):
                raise ValueError('Existing Turbo chain has an extra consumer')
    # Prove the retained MODEL really reaches the supported loader, rather than
    # merely finding its filename in an unrelated branch of the graph.
    probe, visited = link, set()
    while True:
        if (not isinstance(probe, list) or len(probe) != 2 or probe[1] != 0
                or probe[0] not in graph or probe[0] in visited):
            raise ValueError('Unresolved retained MODEL chain')
        visited.add(probe[0])
        inputs = graph[probe[0]]['inputs']
        if 'unet_name' in inputs:
            if Path(inputs['unet_name']).name != BASE:
                raise ValueError('Retained chain uses a different model')
            break
        probe = inputs.get('model')
    if 'h3_turbo4_lora' in graph or 'h3_turbo4_shift' in graph:
        raise ValueError('Output nodes already exist; choose the original source graph')
    for node_id in replaced:
        del graph[node_id]
    graph['h3_turbo4_lora'] = {'class_type': 'LoraLoaderModelOnly', 'inputs': {
        'model': link, 'lora_name': lora_name, 'strength_model': 1.0}}
    graph['h3_turbo4_shift'] = {'class_type': 'MiniMaxH3SigmaShift', 'inputs': {
        'model': ['h3_turbo4_lora', 0], 'shift_video': 6.0, 'shift_audio': 3.0}}
    graph[guider]['inputs']['model'] = ['h3_turbo4_shift', 0]
    graph[scheduler]['inputs'].update(model=['h3_turbo4_shift', 0], steps=4, scheduler='simple', denoise=1.0)
    graph[sampler]['inputs']['sampler_name'] = 'euler'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lora', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.verify_only and (args.input or args.output):
        parser.error('--verify-only cannot write a workflow')
    if not args.verify_only and (not args.input or not args.output):
        parser.error('Supply --input and --output, or use --verify-only')
    try:
        receipt = verify_lora(args.lora)
        if not args.verify_only:
            if args.lora.name != LORA:
                raise ValueError('Verified partial must be finalized to the exact LoRA filename first')
            result = convert(json.loads(args.input.read_text()))
            with args.output.open('x') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                f.write('\n')
            receipt.update(input_sha256=digest(args.input), output_sha256=digest(args.output))
        print(json.dumps({'CPU_only': True, 'GPU_submitted': False, **receipt}, indent=2))
    except (OSError, ValueError) as e:
        parser.exit(1, str(e) + '\n')


if __name__ == '__main__':
    main()
