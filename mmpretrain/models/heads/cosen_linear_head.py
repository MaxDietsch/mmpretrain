# Copyright (c) OpenMMLab. All rights reserved.
from typing import Optional, Tuple, List
from mmpretrain.structures import DataSample
import torch
import torch.nn as nn

from mmpretrain.registry import MODELS
from .linear_head import LinearClsHead
from ..losses.cosen_ce_loss import CoSenCrossEntropyLoss


@MODELS.register_module()
class CoSenLinearClsHead(LinearClsHead):
    """ CoSen Linear classifier head (Cost-Sensitive Learning of Deep Feature Representations from Imbalanced Data).
        Like LinearClsHead but additionally returns the predictions
        which are important for the calculation of the Confusion Matrix.
        
        REQUIRES:
            to have CoSenCrossEntropyLoss as loss_module 
    """

    def __init__(self, **kwargs):

        super(CoSenLinearClsHead, self).__init__(**kwargs)

        if not isinstance (self.loss_module, CoSenCrossEntropyLoss):
            raise TypeError('Loss function of the Head should be of type CoSenLinearClsHead')

        

    def _get_loss(self, cls_score: torch.Tensor,
                  data_samples: List[DataSample], **kwargs):
        """Unpack data samples and compute loss."""
        # Unpack data samples and pack targets
        if 'gt_score' in data_samples[0]:
            # Batch augmentation may convert labels to one-hot format scores.
            target = torch.stack([i.gt_score for i in data_samples])
        else:
            target = torch.cat([i.gt_label for i in data_samples])

        # compute loss
        losses = dict()
        loss = self.loss_module(
            cls_score, target, **kwargs)
        losses['loss'] = loss

        # compute accuracy
        if self.cal_acc:
            assert target.ndim == 1, 'If you enable batch augmentation ' \
                'like mixup during training, `cal_acc` is pointless.'
            acc = Accuracy.calculate(cls_score, target, topk=self.topk)
            losses.update(
                {f'accuracy_top-{k}': a
                 for k, a in zip(self.topk, acc)})

        return losses, cls_score
