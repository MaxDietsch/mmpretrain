import os
import json
import torch 

"""
This script takes a directory (specified_directory).
It goes three directories deeper from the base directory and searches for .json file. 
This procedure is down for every subdirectory on the base directory. 
The script will read the .json files and search for accuracy, precision, recall and f1 scores.
The scores (except accuracy) should be classwise and the average over all found values will be calculated.
The calculated scores will be printed to the screen 
"""

acc = {"lr_0.01": [], 'lr_0.001': [], 'lr_decr': []}
rec = {"lr_0.01": [], 'lr_0.001': [], 'lr_decr': []}
prec = {"lr_0.01": [], 'lr_0.001': [], 'lr_decr': []}
f1 = {"lr_0.01": [], 'lr_0.001': [], 'lr_decr': []}

def find_json_values(root_dir):
    # Walk through the directory structure starting at 'root_dir'
    for d1 in os.listdir(root_dir):
        d1_path = os.path.join(root_dir, d1)
        if os.path.isdir(d1_path):  # Ensure d1 is a directory
            for d2 in os.listdir(d1_path):
                d2_path = os.path.join(d1_path, d2)
                if os.path.isdir(d2_path):  # Ensure d2 is a directory
                    for d3 in os.listdir(d2_path):
                        d3_path = os.path.join(d2_path, d3)
                        if os.path.isdir(d3_path):
                            for file in os.listdir(d3_path):
                                if file.endswith('.json'):
                                    file_path = os.path.join(d3_path, file)
                                    with open(file_path, 'r') as json_file:
                                        try:
                                            data = json.load(json_file)
                                            # Assuming 'accuracy' and 'recall' are top-level keys in the JSON file
                                            accuracy = data.get('accuracy/top1', 'N/A')
                                            recall = data.get('single-label/recall_classwise', 'N/A')
                                            precision = data.get('single-label/precision_classwise', 'N/A')
                                            f1_score = data.get('single-label/f1-score_classwise', 'N/A')
                                            acc[d1].append(torch.tensor(accuracy))
                                            rec[d1].append(torch.tensor(recall))
                                            prec[d1].append(torch.tensor(precision))
                                            f1[d1].append(torch.tensor(f1_score))

                                            #print(f"{d1}: Accuracy: {accuracy}, Recall: {recall}\n")
                                        except json.JSONDecodeError:
                                            print(f"Error reading JSON file: {file_path}")
    # Print the separator line
    print('reading finished')

def calculate_average():

    for key in acc: 
        #print(torch.stack(acc[key]))
        acc_temp = torch.mean(torch.stack(acc[key]), dim = 0)
        #print(acc_temp)

        #print(torch.stack(rec[key]))
        rec_temp = torch.mean(torch.stack(rec[key]), dim = 0)
        #print(rec_temp)

        #print(torch.stack(prec[key]))
        prec_temp = torch.mean(torch.stack(prec[key]), dim = 0)
        #print(prec_temp)

        #print(torch.stack(f1[key]))
        f1_temp = torch.mean(torch.stack(f1[key]), dim = 0) 
        #print(f1_temp)
        
        
        with open(txt_path, 'a') as file:
            file.write(f"\n\nModel: {model} with schedule: {key} \n")
            
            metrics = ['Accuracy:', 'Classwise Recall:', 'Classwise Precision:', 'Classwise F1-Score:']
            
            tensors = [acc_temp, rec_temp, prec_temp, f1_temp]
            
            for metric, tensor in zip(metrics, tensors):
                rounded_tensor = torch.round(tensor * 10000) / 10000
                tensor_str = rounded_tensor.cpu().numpy().tolist()
                file.write(f"{metric} \t {tensor_str} \n")
            

# Example usage
specified_directory = "../work_dirs/phase1/resnet50/test"
txt_path = '../work_dirs/phase1/results.txt'
model = 'ResNet50'
find_json_values(specified_directory)
calculate_average()

print('The results are written to the specified file!')
