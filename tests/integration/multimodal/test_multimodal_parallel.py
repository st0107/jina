import os

import pytest
import numpy as np

from jina.flow import Flow
from jina.proto import jina_pb2
from jina.drivers.helper import array2pb, pb2array

NUM_DOCS = 100
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def multimodal_documents():
    docs = []
    for idx in range(0, NUM_DOCS):
        """
        doc - idx
            |
            | - chunk - blob [idx, idx] - modality1 -> The dummy encoder will pass the blob to embedding
            | - chunk - blob [idx, idx, idx] - modality2 -> The dummy encoder will pass the blob to embedding
        Result:
            doc - idx - embedding [idx, idx, idx, idx, idx]
        """
        doc = jina_pb2.Document()
        doc.text = f'{idx}'

        for modality in ['modality1', 'modality2']:
            chunk = doc.chunks.add()
            chunk.modality = modality
            if modality == 'modality1':
                chunk.blob.CopyFrom(array2pb(np.array([idx, idx])))
            else:
                chunk.blob.CopyFrom(array2pb(np.array([idx, idx, idx])))
        docs.append(doc)
    return docs


def test_multimodal_embedding_parallel(multimodal_documents):
    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for idx, doc in enumerate(resp.index.docs):
            np.testing.assert_almost_equal(
                pb2array(doc.embedding), np.array([idx, idx, idx, idx, idx])
            )

    with Flow().load_config(
        os.path.join(cur_dir, 'flow-embedding-multimodal-parallel.yml')
    ) as index_gt_flow:
        index_gt_flow.index(input_fn=multimodal_documents, output_fn=validate_response)


@pytest.fixture
def multimodal_all_types_documents():
    docs = []
    for idx in range(0, NUM_DOCS):
        """
        doc - idx
            |
            | - chunk - embedding [idx, idx] - modality1
            | - chunk - blob [idx, idx, idx] - modality2
            | - chunk - text 'modality3' - modality3 -> Inside multimodal encoder will be encoded into [3, 3]
            | - chunk - buffer b'modality4' - modality4 -> Inside multimodal encoder will be encoded into [4, 4]
        Result:
            doc - idx - embedding [idx, idx, idx, idx, idx, 3, 3, 4, 4]
        """
        doc = jina_pb2.Document()
        doc.text = f'{idx}'

        for modality in ['modality1', 'modality2', 'modality3', 'modality4']:
            chunk = doc.chunks.add()
            chunk.modality = modality
            if modality == 'modality1':
                chunk.embedding.CopyFrom(array2pb(np.array([idx, idx])))
            elif modality == 'modality2':
                chunk.blob.CopyFrom(array2pb(np.array([idx, idx, idx])))
            elif modality == 'modality3':
                chunk.text = 'modality3'
            elif modality == 'modality4':
                chunk.buffer = 'modality4'.encode()
        docs.append(doc)
    return docs


def test_multimodal_all_types_parallel(multimodal_all_types_documents):
    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for idx, doc in enumerate(resp.index.docs):
            np.testing.assert_almost_equal(
                pb2array(doc.embedding), np.array([idx, idx, idx, idx, idx, 3, 3, 4, 4])
            )

    with Flow().load_config(
        os.path.join(cur_dir, 'flow-multimodal-all-types-parallel.yml')
    ) as index_gt_flow:
        index_gt_flow.index(
            input_fn=multimodal_all_types_documents, output_fn=validate_response
        )
