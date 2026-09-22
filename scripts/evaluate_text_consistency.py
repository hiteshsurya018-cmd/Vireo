
import argparse, sys
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
sys.path.insert(0,str(Path(__file__).parents[1]/"app"))
from data import load_tables, prepare
p=argparse.ArgumentParser(); p.add_argument("--data-dir",required=True); p.add_argument("--out",default="outputs/evaluation.json"); args=p.parse_args()
t,_=prepare(load_tables(args.data_dir))
docs=t.customer_message.fillna("").map(lambda s: __import__("re").sub(r"vr\d+|\d+"," ",str(s).lower()))
v=TfidfVectorizer(stop_words="english",ngram_range=(1,2),min_df=5,max_features=5000,sublinear_tf=True)
Xtr_text,Xte_text,ytr,yte=train_test_split(docs,t.category,test_size=.2,random_state=42,stratify=t.category)
Xtr=v.fit_transform(Xtr_text)
Xte=v.transform(Xte_text)
clf=LogisticRegression(max_iter=1000,C=2); clf.fit(Xtr,ytr); pred=clf.predict(Xte)
out={"holdout_n":int(len(yte)),"agreement":float(accuracy_score(yte,pred)),"disagreement":float(1-accuracy_score(yte,pred)),
     "note":"Agreement with exported intake category; not ground-truth accuracy.",
     "common_confusions":{}}
cm=confusion_matrix(yte,pred,labels=sorted(t.category.unique()))
labels=sorted(t.category.unique())
pairs=[]
for i,a in enumerate(labels):
    for j,b in enumerate(labels):
        if i!=j and cm[i,j]:
            pairs.append((int(cm[i,j]),a,b))
out["common_confusions"]={f"{a} -> {b}":n for n,a,b in sorted(pairs,reverse=True)[:8]}
Path(args.out).parent.mkdir(parents=True,exist_ok=True)
import json; json.dump(out,open(args.out,"w"),indent=2); print(json.dumps(out,indent=2))
