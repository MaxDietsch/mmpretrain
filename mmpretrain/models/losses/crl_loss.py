# Copyright (c) OpenMMLab. All rights reserved.
import torch.nn as nn
import torch.nn.functional as F

from mmpretrain.registry import MODELS
from .utils import weight_reduce_loss

import heapq


def cross_entropy(pred,
                  label,
                  weight=None,
                  reduction='mean',
                  avg_factor=None,
                  class_weight=None):
    """Calculate the CrossEntropy loss.

    Args:
        pred (torch.Tensor): The prediction with shape (N, C), C is the number
            of classes.
        label (torch.Tensor): The gt label of the prediction.
        weight (torch.Tensor, optional): Sample-wise loss weight.
        reduction (str): The method used to reduce the loss.
        avg_factor (int, optional): Average factor that is used to average
            the loss. Defaults to None.
        class_weight (torch.Tensor, optional): The weight for each class with
            shape (C), C is the number of classes. Default None.

    Returns:
        torch.Tensor: The calculated loss
    """
    # element-wise losses
    loss = F.cross_entropy(pred, label, weight=class_weight, reduction='none')

    # apply weights and do the reduction
    if weight is not None:
        weight = weight.float()
    loss = weight_reduce_loss(
        loss, weight=weight, reduction=reduction, avg_factor=avg_factor)

    return loss


@MODELS.register_module()
class CRLLoss(nn.Module):
    """ Loss has a lot of similarities with CrossEntropyLoss
        Loss based on epoch-based training based on: 
        Imbalanced Deep Learning by Minority Class Incremental Rectification by Qi Dong et al.
        (only class based sampling with relative comparison)
        Requirements: 
            new (non-default parameters in the init)

    Args:
        min_classes (List[int]): The labels of the minority classes for the algorithm (only
            these will be used for mining hard samples, in the paper there is a criterion for that)
        k (int): The k in top-k mining (how many hard positives and negatives will be mined)
        use_sigmoid (bool): Whether the prediction uses sigmoid
            of softmax. Defaults to False.
        use_soft (bool): Whether to use the soft version of CrossEntropyLoss.
            Defaults to False.
        reduction (str): The method used to reduce the loss.
            Options are "none", "mean" and "sum". Defaults to 'mean'.
        loss_weight (float):  Weight of the loss. Defaults to 1.0.
        class_weight (List[float], optional): The weight for each class with
            shape (C), C is the number of classes. Default None.
        pos_weight (List[float], optional): The positive weight for each
            class with shape (C), C is the number of classes. Only enabled in
            BCE loss when ``use_sigmoid`` is True. Default None.
    """

    def __init__(self,
                 min_classes, 
                 k, 
                 use_sigmoid=False,
                 use_soft=False,
                 reduction='mean',
                 loss_weight=1.0,
                 class_weight=None,
                 pos_weight=None):
        super(CRLLoss, self).__init__()
        self.use_sigmoid = use_sigmoid
        self.use_soft = use_soft
        assert not (
            self.use_soft and self.use_sigmoid
        ), 'use_sigmoid and use_soft could not be set simultaneously'

        self.reduction = reduction
        self.loss_weight = loss_weight
        self.class_weight = class_weight
        self.pos_weight = pos_weight

        if self.use_sigmoid:
            self.cls_criterion = binary_cross_entropy
        elif self.use_soft:
            self.cls_criterion = soft_cross_entropy
        else:
            self.cls_criterion = cross_entropy

        self.k = k 
        self.min_classes = torch.tensor(min_classes) 

    def forward(self,
                cls_score,
                label,
                weight=None,
                avg_factor=None,
                reduction_override=None,
                **kwargs):
        assert reduction_override in (None, 'none', 'mean', 'sum')
        reduction = (
            reduction_override if reduction_override else self.reduction)

        if self.class_weight is not None:
            class_weight = cls_score.new_tensor(self.class_weight)
        else:
            class_weight = None

        # only BCE loss has pos_weight
        if self.pos_weight is not None and self.use_sigmoid:
            pos_weight = cls_score.new_tensor(self.pos_weight)
            kwargs.update({'pos_weight': pos_weight})
        else:
            pos_weight = None

        
        ### MINE HARD SAMPLES

        print(cls_score)
        print(label)
        
        # get mask of where the min_class examples are in the batch 
        min_labels_mask = torch.isin(label, self.min_classes)
        print(min_labels_mask)
        
        # get the indices of the location of min_classes in the batch
        ind = torch.where(min_labels_mask)
        print(ind)

        # get tensor where to store the hard samples, 0 -> hard negatives, 1-> hard positives 
        hard_samples = [[[] for _ in range(len(ind)) ] for _ in range(2)]

        ## MINE HARD NEGATIVES

        # get label for which the maximum prediction was made and the maximum prediction score
        max_pred, max_pred_lab = cls_score[min_labels_mask].max(dim=1)
        print(max_pred_lab)

        # check if predictions are wrong
        max_thrs_mask = torch.ne(max_pred_lab, labels[ind])
        print(max_thrs_mask)

        # get indices where wrong prediction scores are made 
        hard_neg_ind = torch.nonzero(max_thrs_mask)
        print(hard_ned_ind)

        # write hard negative samples into hard_samples)
        for i, idx in enumerate(hard_ned_ind):
            if (len(hard_samples[0][max_pred_lab[idx]]) >= self.k) and  (max_pred[idx] > hard_samples[0][max_pred_lab[idx]][0][0]:
                heapq.heappop(hard_samples[0][max_pred_lab[idx]])
                heapq.heappush(hard_samples[0][max_pred_lab[idx]], [max_pred[lab], idx])
            elif len(hard_samples[0][max_pred_lab[idx]]) < self.k:
                heapq.heappush(hard_samples[0][max_pred_lab[idx]], [max_pred[lab], idx])
        print(hard_samples)







        loss_cls = self.loss_weight * self.cls_criterion(
            cls_score,
            label,
            weight,
            class_weight=class_weight,
            reduction=reduction,
            avg_factor=avg_factor,
            **kwargs)
        return loss_cls