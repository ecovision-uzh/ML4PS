# ML4PS
Repository for the Introduction to Machine Learning in Plant Sciences course (Modules 1 &amp; 2)

## Setup instruction

This course uses **git** and **conda**. **git** and **conda** are standard tools for Machine Learning development in Python (and far beyond). There are many resources and tutorials online, if you want to learn more.  

If you have never used **git** and **conda**, the following instruction explain how to set them up on your device. The following sections will walk you through how to clone the repository to have the code on your device, how to create the virtual environment for the course dependencies for the course and how to run the code locally on your machine.

If you do not want to use **git** and/or **conda**, we also point to alternative ways to download the code and create an environment for the course. *We nevertheless encourage you to learn these tools - if you do not know them already.*

### Downloading code

The code for this course is hosted on the [EcoVision GitHub page](https://github.com/ecovision-uzh/ML4PS). It can be downloaded directly as a zip file or by using **git** clone. 

To download the code through **git**, you need to have **git** installed on your device. You can download **git** by following the instructions from [git-scm](https://git-scm.com/install/linux) for your device. You do not need a GitHub account to clone the repository. 

Once **git** is installed on your device you can clone the repository to your device by running on your favorite command line interface: 

```bash
git clone https://github.com/ecovision-uzh/ML4PS.git
``` 

If you prefer not using command line, you can also clone the repository via [GitHub Desktop](https://docs.github.com/en/desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop).

If you prefer not using **git**, you can download the repository via Code > download ZIP on the [GitHub page](https://github.com/ecovision-uzh/ML4PS) and unzip it on your device. 

### Setting up the environment

The content of this course was designed and tested using the **conda** environment ``ML4PSenv``. This section explains how to replicate it locally on your machine. To ensure you avoid any dependency issues, we recommend using the course environment. 

If you do not have **conda** set up on your device, follow the instructions from [Anaconda](https://www.anaconda.com/docs/getting-started/miniconda/install) to install Miniconda on your device.

To create the environment on your devive, once **conda** is set up, navigate to the the root folder of the ML4PS repository and run this command on your favorite command line interface:

```bash
conda env create -f 0-Setup/ML4PSrequirements.yml
``` 

If you prefer not using **conda**, you can create an environment with your favorite environment manager (**venv**, **uv**...) using the requirements file  (``0-Setup/ML4PSrequirements.yml`` or ``0-Setup/ML4PSrequirements.txt``) or manually installing the packages (**numpy**, **pandas**, **sklearn**, **pytorch**...) with the appropriate versions.

### Installing an IDE

The code for this course consists mainly of **jupyter** notebooks. Jupyter notebooks are a handy way of writing, testing, and documenting **python** code. To read and run notebooks seamlessly you need to download and set up an Integrated Development System if you do not already have one on your computer. You may choose the IDE of your liking, here are several standard options and their download link:

- [Visual Studio Code](https://code.visualstudio.com/download) (with the Jupyter extension)
- [PyCharm](https://www.jetbrains.com/pycharm/download/) (with the Markdown plugin)
- Anaconda's [Spyder](https://www.anaconda.com/docs/getting-started/working-with-conda/ide-tutorials/spyder) (make sure to add ``spyder-notebook`` to your environment)

With this you should be all setup and ready to go! If ever you have any problem setting up, don't sweat, we will be there to help you with any issues you may have encountered during the setup on the first exercise session. If you have any feedback, on the setup and/or on the course, we are happy to hear it! Enjoy!

### Google Colab access

If you have problems setting up the environment locally, you can run the notebooks in **Google Colab** instead.  
To use Colab, you need a **Google account**.

Available notebooks:

- [Lab 2. Linear Regression](https://colab.research.google.com/drive/1wKMVGbBtlE6WLirXwoam6hCOVeEi7Vmq?usp=sharing)
- [Lab3. Classification and Clustering](https://colab.research.google.com/drive/1CFg9cVsB0s5i8TzGVXZpsSf2keOWOKaP?usp=sharing)
- [Lab 4. Deep Learning](https://colab.research.google.com/drive/1nj2ix-j9NGelsxnpNE5qh3YdtC_tdCst?usp=sharing)

To use a notebook in your own workspace:

1. Open the link in your browser.
2. Make sure you are logged into your Google account.
3. In the menu, go to **File → Save a copy in Drive**.  
   This will save a personal copy of the notebook in your Google Drive.
4. Make sure you have enough free space in your Google Drive to store the notebook and any generated files.

