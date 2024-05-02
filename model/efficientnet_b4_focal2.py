model = dict(
    type='ImageClassifier',
    backbone=dict(type='EfficientNet', arch='b4'),
    neck=dict(type='GlobalAveragePooling'),
    head=dict(
        type='LinearClsHead',
        num_classes=4,
        in_channels=1792,
        loss=dict(type='MultiClassFocalLoss', gamma = 1),
        topk=(1),
    ))
