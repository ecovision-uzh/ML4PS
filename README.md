# ML4PS
Repository for the Introduction to Machine Learning in Plant Sciences course (Modules 1 &amp; 2)

## Setup instruction

This course uses **git** and **conda**. **git** and **conda** are standard tools for Machine Learning development in Python (and beyond). There are many resources and tutorials online, if you want to learn more.  

If you have never used **git** and **conda**, the following instruction explain how to set them up on your device, how to clone the repository to have the code on your device, how to create the environment for the course and how to run the code.

If you do not want to use **git** and/or **conda**, we additionally point to alternative ways to download the code and create an environment for the course.

### Downloading code

The code for this course is hosted on the [Ecovision GitHub page](https://github.com/ecovision-uzh/ML4PS). It can be downloaded directly or using **git**. 

To download the code through **git**, you need to have **git** on your device. You can download **git** by following the instructions from [git-scm](https://git-scm.com/install/linux) for your device. You do not need a GitHub account to clone the repository. 

Once **git** is installed on your device you can clone the repository to your device by running on your favorite command line interface: ``git clone https://github.com/ecovision-uzh/ML4PS.git``. If you prefer not using command line, you can also clone the repository via [GitHub Desktop](https://docs.github.com/en/desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop).

If you prefer not using **git**, you can download the repository via Code > download ZIP on the [GitHub page](https://github.com/ecovision-uzh/ML4PS) and unzip it on your device. 

### Setting up the environment

For this course we are using a **conda** environment. To ensure you avoid any technical issues, we recommend you use the course environment. 

If you do not have **conda** setup on your device, follow instructions from [Anaconda](https://www.anaconda.com/docs/getting-started/miniconda/install) to install Miniconda on your device.

To create the environment on your devive, once **conda** is setup, navigate to the folder ML4PS and run on your favorite command line interface ``conda env create -f 0-Setup/ML4PSrequirements.yml`` (from the root of the repository). 

If you prefer not using **conda**, you can create an environment with your favorite environment manager (**venv**, **uv**...) using the requirements file  (``0-Setup/ML4PSrequirements.yml`` or ``0-Setup/ML4PSrequirements.txt``) or manually installing the packages (**numpy**, **pandas**, **sklearn**, **pytorch**...).

### Installing an IDE

The code for this course consists mainly of **jupyter** notebooks. To read and run notebooks seamlessly you need to download and setup an Integrated Development System if you do not already have one on your computer. You may choose the IDE of your liking, here are several standard options and their download link:

- [Visual Studio Code](https://code.visualstudio.com/download) (with the Jupyter extension)
- [Pycharm](https://www.jetbrains.com/pycharm/download/) (with the Markdown plugin)
- Anaconda's [Spyder](https://www.anaconda.com/docs/getting-started/working-with-conda/ide-tutorials/spyder) (make sure to add ``spyder-notebook`` to your environment)