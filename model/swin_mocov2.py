model = dict(
    type='MoCo',
    queue_len=512,
    feat_dim=128,
    momentum=0.999,
    backbone=dict(
        type='SwinTransformer',
        arch = 'small',
        img_size = 640),
    neck=dict(
        type='MoCoV2Neck',
        in_channels=2048,
        hid_channels=2048,
        out_channels=128,
        with_avg_pool=True),
    head=dict(
        type='ContrastiveHead',
        loss=dict(type='mmcls.CrossEntropyLoss'),
        temperature=0.2))
