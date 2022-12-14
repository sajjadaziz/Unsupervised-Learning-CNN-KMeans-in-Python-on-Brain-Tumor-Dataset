# -*- coding: utf-8 -*-
"""Unsupervised Learning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Zwjz7rnZyw0OAPjp575vL_mYCr90Om0B
"""

import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import tensorflow as tf
import cv2
import os
import seaborn as sn; sn.set(font_scale=1.4)
from sklearn.metrics import confusion_matrix
from sklearn.utils import shuffle
from tqdm import tqdm
from keras.preprocessing.image import load_img 
from keras.preprocessing.image import img_to_array 
from keras.applications.vgg16 import preprocess_input
from keras.applications.vgg16 import VGG16 
from keras.models import Model
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from random import randint
from tensorflow import keras

"""**Brain Tumor Dataset**
https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset

**Convolutional Neural Networks**
"""

class_names = ['glioma', 'meningioma', 'notumor', 'pituitary']
class_names_label = {class_name:i for i, class_name in enumerate(class_names)}
nb_classes = len(class_names)
IMAGE_SIZE = (150, 150)

def load_data():
    datasets = ['/content/drive/MyDrive/tumor/Training', '/content/drive/MyDrive/tumor/Testing']
    output = []
    for dataset in datasets:
        images = []
        labels = []
        print("Loading {}".format(dataset))
        for folder in os.listdir(dataset):
            label = class_names_label[folder]
            for file in tqdm(os.listdir(os.path.join(dataset, folder))):
                img_path = os.path.join(os.path.join(dataset, folder), file)
                image = cv2.imread(img_path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image = cv2.resize(image, IMAGE_SIZE) 
                images.append(image)
                labels.append(label)
        images = np.array(images, dtype = 'float32')
        labels = np.array(labels, dtype = 'int32')   
        output.append((images, labels))
    return output

(train_images, train_labels), (test_images, test_labels) = load_data()

train_images, train_labels = shuffle(train_images, train_labels, random_state=25)
train_images = train_images / 255.0 
test_images = test_images / 255.0

n_train = train_labels.shape[0]
n_test = test_labels.shape[0]

print ("Number of training examples: {}".format(n_train))
print ("Number of testing examples: {}".format(n_test))
print ("Each image is of size: {}".format(IMAGE_SIZE))

model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(16, (3, 3), activation = 'relu', input_shape = (150, 150, 3)), 
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(32, (3, 3), activation = 'relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(64, (3, 3), activation = 'relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation=tf.nn.relu),
    tf.keras.layers.Dense(4, activation=tf.nn.softmax)
])

model.compile(optimizer = "adam", loss = 'sparse_categorical_crossentropy', metrics=['accuracy'])
history = model.fit(train_images, train_labels, batch_size=128, epochs=20, validation_split = 0.2)

model.save('/content/drive/MyDrive/model')

predictions = model.predict(test_images)
pred_labels = np.argmax(predictions, axis = 1)

CM = confusion_matrix(test_labels, pred_labels)
ax = plt.axes()
sn.heatmap(CM, annot=True, 
           annot_kws={"size": 10}, 
           xticklabels=class_names, 
           yticklabels=class_names, ax = ax)
ax.set_title('Confusion matrix')
plt.show()

"""**K-Means**"""

# model = keras.models.load_model('/content/drive/MyDrive/model')

model = VGG16()
model = Model(inputs = model.inputs, outputs = model.layers[-2].output)

datasets = ['/content/drive/MyDrive/tumor/Training', '/content/drive/MyDrive/tumor/Testing']
images = []
for dataset in datasets:
  for folder in os.listdir(dataset):
    path = dataset + '/' + folder
    with os.scandir(path) as files:
      for file in files:
        images.append(path + '/' + file.name)

def extract_features(file, model):
    img = load_img(file, target_size=(224, 224))
    img = np.array(img)
    reshaped_img = img.reshape(1,224, 224,3)
    imgx = preprocess_input(reshaped_img)
    features = model.predict(imgx, use_multiprocessing=True)
    return features

data = {}
for image in images:
    feat = extract_features(image,model)
    data[image] = feat

a_file = open("/content/drive/MyDrive/model/data.pkl", "wb")
pickle.dump(data, a_file)
a_file.close()
# a_file = open("/content/drive/MyDrive/model/data.pkl", "rb")
# data = pickle.load(a_file)
# a_file.close()

filenames = np.array(list(data.keys()))
feat = np.array(list(data.values()))

feat = feat.reshape(-1,4096)
unique_labels = int(len(images)/100)

pca = PCA(n_components=1000, random_state=22)
pca.fit(feat)
x = pca.transform(feat)

SSE = []
for cluster in range(2,unique_labels):
    kmeans = KMeans(n_clusters = cluster, init='k-means++')
    kmeans.fit(x)
    SSE.append(kmeans.inertia_)

frame = pd.DataFrame({'Cluster':range(2,unique_labels), 'SSE':SSE})
plt.figure(figsize=(unique_labels,unique_labels/2))
plt.plot(frame['Cluster'], frame['SSE'], marker='o')
plt.xlabel('Number of clusters')
plt.ylabel('Inertia')

kmeans = KMeans(n_clusters=unique_labels, random_state=22)
labels = kmeans.fit(x)

groups = {}
for file, cluster in zip(filenames,kmeans.labels_):
    if cluster not in groups.keys():
        groups[cluster] = []
        groups[cluster].append(file)
    else:
        groups[cluster].append(file)

def view_cluster(cluster):
    plt.figure(figsize = (25,25));
    files = groups[cluster]
    if len(files) > 30:
        print(f"Clipping cluster size from {len(files)} to 30")
        files = files[:29]
    for index, file in enumerate(files):
        plt.subplot(10,10,index+1);
        img = load_img(file)
        img = np.array(img)
        plt.imshow(img)
        plt.axis('off')

view_cluster(0)

view_cluster(1)

view_cluster(2)

view_cluster(3)

view_cluster(4)