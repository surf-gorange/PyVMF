from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='pyvmf',
      version='0.0.1',
      description='A python VMF parser',
      long_description=readme(),
      url='https://github.com/GorangeNinja/PyVMF',
      author='Noah "GorangeNinja"',
      author_email='flyingcircus@example.com',
      license='MIT',
      packages=['pyvmf'],
      zip_safe=False)
