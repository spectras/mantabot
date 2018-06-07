#include <Python.h>
#include <sys/prctl.h>

static PyObject * get_proc_name(PyObject * self, PyObject * dummy)
{
    char buffer[16];
    if (prctl(PR_GET_NAME, buffer) < 0) {
        PyErr_SetFromErrno(PyExc_OSError);
        return NULL;
    }
    return PyUnicode_FromString(buffer);
}

static PyObject * set_proc_name(PyObject * self, PyObject * name)
{
    if (!PyUnicode_Check(name)) {
        PyErr_SetString(PyExc_TypeError, "name must be a string");
        return NULL;
    }
    if (prctl(PR_SET_NAME, PyUnicode_AsUTF8(name)) < 0) {
        PyErr_SetFromErrno(PyExc_OSError);
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyMethodDef module_methods[] = {
    {
        "get_proc_name",
        get_proc_name,
        METH_NOARGS,
        "Get process name"
    },
    {
        "set_proc_name",
        set_proc_name,
        METH_O,
        "Set process name from string"
    }
};

static PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "native",
    "C wrapper for features unavailable from python",
    0,
    module_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyObject * PyInit_native() { return PyModule_Create(&module_def); }
