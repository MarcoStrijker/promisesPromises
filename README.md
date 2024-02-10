# promisesPromises

## Description
This application is an effort to identify differences in the language use in the manifestos of all Dutch political parties in recent years.

## Installation
This application is made in Python 3.11.6. To install the required packages, run the following command in the terminal (in the project root):

First, create a virtual environment:
```
python -m venv venv
```

Then, activate the virtual environment:
```
venv/bin/activate
```

Then, install the required packages:
```
pip install -r requirements.txt
```

## Data structure
Currently, only the manifestos of the Tweede Kamer elections are supported. All manifestos should be in pdf format. All the manifestos will be automatically identified when manifests of new Tweede Kamer elections are added. Adding TK elections is as easy as adding a directory with the year and month of the election (for example, 2017-03) within TK and adding the pdf files of the parties to that directory. The data folder has the following structure:
```
data
├── manifests
│   ├── <Abbreviation of the type of election>
│   │   ├── <Year-month of the election>
│   │   │   ├── <The program with the name of the party> 
```

This could look like this:
```
data
├── manifests
│   ├── TK
│   │   ├── 2017-03
│   │   │   ├── CDA.pdf
```
