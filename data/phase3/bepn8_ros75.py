#construct dataloader and evaluator
dataset_type = 'CustomDataset'
data_preprocessor = dict(
    # Input image data channels in 'RGB' order
    mean=[151.14, 102.69, 97.74],
    std=[70.03, 55.91, 54.73],
    to_rgb=True,
)

train_pipeline = [
    dict(type='LoadImageFromFile'),     # read image
    dict(type='Resize', scale=(640, 640), interpolation='bicubic'),
    dict(type='PackInputs'),         # prepare images and labels
]

test_pipeline = [
    dict(type='LoadImageFromFile'),     # read image
    dict(type='Resize', scale=(640, 640), interpolation='bicubic'),
    dict(type='PackInputs'),                 # prepare images and labels
]

train_dataloader = dict(
    batch_size=8,
    num_workers=5,
    dataset=dict(
        type=dataset_type,
        data_root='../../B_E_P_N_aug',
        ann_file='meta/train.txt',
        data_prefix='train',
        with_label=True,
        classes=['normal', 'polyps', 'barretts', 'esophagitis'],
        pipeline=train_pipeline),
        sampler=dict(type='CoSenROSSampler', ros_pct = 0.75, rus_maj_pct = 0.8, shuffle=True),
    persistent_workers=True,
)

val_dataloader = dict(
    batch_size=8,
    num_workers=5,
    dataset=dict(
        type=dataset_type,
        data_root='../../B_E_P_N',
        ann_file='meta/test.txt',
        data_prefix='test',
        with_label=True,
        classes=['normal', 'polyps', 'barretts', 'esophagitis'],
        pipeline=test_pipeline),
    sampler=dict(type='DefaultSampler', shuffle=False),
    persistent_workers=True,
)
val_evaluator = [
        dict(type='Accuracy', topk=(1)),
        dict(type='SingleLabelMetric', items=['precision', 'recall', 'f1-score'], average=None)
                ]

test_dataloader = val_dataloader
test_evaluator = val_evaluator

