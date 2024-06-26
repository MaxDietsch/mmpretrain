optim_wrapper = dict(
    optimizer=dict(type='SGD', lr=0.01, momentum=0.9, weight_decay=0.0001))

param_scheduler = dict(
    type='MultiStepLR', by_epoch=True, milestones=[30, 60, 90], gamma=0.1)

samples_per_class = [3312, 45, 132, 539]
alpha = 0.3
train_cfg = dict(by_epoch=5, samples_per_class = samples_per_class, alpha = alpha, max_epochs=100, val_interval=1)

val_cfg = dict()
test_cfg = dict()

# If you use a different total batch size, like 512 and enable auto learning rate scaling.
# We will scale up the learning rate to 2 times.
#auto_scale_lr = dict(base_batch_size=256)

