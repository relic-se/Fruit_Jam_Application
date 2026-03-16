# Fruit_Jam_Application
Template for a CircuitPython application for the Adafruit Fruit Jam which is compatible with Fruit Jam OS.

## Building CircuitPython Package
Ensure that you have python 3.x installed system-wide and all the prerequisite libraries installed using the following command:

``` shell
pip3 install circup requests
```

Download all CircuitPython libraries and package the application using the following command:

``` shell
python3 build/build.py
```

The project bundle should be found within `./dist` as a `.zip` file with the same name as your repository.

## Testing with Blinka
Ensure that you have python 3.x installed system-wide and all the prerequisite libraries installed using the following command:

``` shell
pip3 install -r requirements-blinka.txt
```

Run the program using the following command:

``` shell
python3 code.py
```

A application window for the program will open and support input from keyboard, mouse, and supported gamepads.
