"""Isolated CPU graph invariants; no model allocation, downloads or GPU calls."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import prepare_turbo4 as tool


def fixture(turbo=True):
    g = {
        '1': {'class_type': 'UNETLoaderMultiGPU', 'inputs': {'unet_name': tool.BASE}},
        '18': {'class_type': 'ExistingModelWrapper', 'inputs': {'model': ['1', 0]}},
        '6': {'class_type': 'MiniMaxH3ImageToVideo', 'inputs': {
            'prompt': '<d>[Chinese] 爷爷！真的是你吗！</d>', 'width': 576, 'height': 1024, 'length': 158}},
        '8': {'class_type': 'BasicGuider', 'inputs': {'model': ['18', 0]}},
        '11': {'class_type': 'BasicScheduler', 'inputs': {'model': ['18', 0], 'steps': 14}},
        '10': {'class_type': 'KSamplerSelect', 'inputs': {'sampler_name': 'res_multistep'}},
        '9': {'class_type': 'RandomNoise', 'inputs': {'noise_seed': 12345}},
    }
    if turbo:
        g['19'] = {'class_type': 'LoraLoaderModelOnly', 'inputs': {'model': ['18', 0], 'lora_name': tool.OLD_LORA, 'strength_model': 1.0}}
        g['20'] = {'class_type': 'MiniMaxH3SigmaShift', 'inputs': {'model': ['19', 0], 'shift_video': 12.0, 'shift_audio': 3.0}}
        g['8']['inputs']['model'] = g['11']['inputs']['model'] = ['20', 0]
    return g


class ConvertTests(unittest.TestCase):
    def test_convert_preserves_source_and_generation_content(self):
        for turbo in [True, False]:
            source = fixture(turbo); before = copy.deepcopy(source)
            out = tool.convert(source)
            self.assertEqual(source, before)
            for k in ['1', '18', '6', '9']:
                self.assertEqual(out[k], source[k])
            self.assertEqual(out['8']['inputs']['model'], out['11']['inputs']['model'])
            self.assertEqual(out['11']['inputs']['steps'], 4)
            self.assertEqual(out['h3_turbo4_shift']['inputs']['shift_video'], 6)
            self.assertEqual(out['h3_turbo4_lora']['inputs']['model'], ['18', 0])
            self.assertNotIn('19', out)

    def test_wrapped_api_preserves_metadata(self):
        out = tool.convert({'prompt': fixture(), 'client_id': 'cpu-test'})
        self.assertEqual(out['client_id'], 'cpu-test')

    def test_ref_unknown_model_lora_and_ambiguous_chains_rejected(self):
        for change in ['reference', 'base', 'lora', 'split', 'extra_consumer', 'duplicate', 'cycle', 'unconnected']:
            g = fixture()
            if change == 'reference': g['6']['class_type'] = 'MiniMaxH3ReferenceToVideo'
            if change == 'base': g['1']['inputs']['unet_name'] = 'other.safetensors'
            if change == 'lora': g['19']['inputs']['lora_name'] = 'other.safetensors'
            if change == 'split': g['11']['inputs']['model'] = ['18', 0]
            if change == 'extra_consumer': g['other'] = {'class_type': 'Consumer', 'inputs': {'model': ['20', 0]}}
            if change == 'duplicate': g['duplicate'] = copy.deepcopy(g['11'])
            if change == 'cycle': g['19']['inputs']['model'] = ['20', 0]
            if change == 'unconnected': g['18']['inputs']['model'] = ['missing', 0]
            with self.subTest(change=change), self.assertRaises(ValueError): tool.convert(g)

    def test_incomplete_and_same_size_wrong_sha_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'fixture';p.write_bytes(b'cpu')
            with self.assertRaisesRegex(ValueError, 'byte count'): tool.verify_lora(p)
            with patch.object(tool, 'SIZE', 3):
                with self.assertRaisesRegex(ValueError, 'SHA256'): tool.verify_lora(p)


if __name__ == '__main__':
    unittest.main()
