model = dict(
    type='ImageClassifier',
    backbone=dict(
        type='SwinTransformer',
        arch='small',
        img_size=640,
        ),
    neck=dict(type='GlobalAveragePooling'),
    head=dict(
        type='LinearClsHead',
        num_classes=3,
        in_channels=768,
        loss=dict(type='CrossEntropyLoss', loss_weight = 1.0),
        topk=(1)
        )
)
