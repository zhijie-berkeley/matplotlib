#include <Python.h>
#include <numpy/arrayobject.h>

static PyObject* mplutil_transform_scale(PyObject* self, PyObject* args)
{
    PyArrayObject* mtx;
    double sx, sy;
    if (!PyArg_ParseTuple(args, "O!dd", &PyArray_Type, &mtx, &sx, &sy)) {
        return NULL;
    }
    npy_intp* dims = PyArray_DIMS(mtx);
    if ((NPY_ARRAY_CARRAY & ~PyArray_FLAGS(mtx))
            || (PyArray_NDIM(mtx) != 2) || (dims[0] != 3) || (dims[1] != 3)
            || (PyArray_TYPE(mtx) != NPY_DOUBLE)) {
        PyErr_SetString(
                PyExc_ValueError,
                "Only C-contiguous 3x3 double arrays are supported");
        return NULL;
    }
    double* data = (double*)PyArray_DATA(mtx);
    // Assume that mtx is a valid transformation matrix; i.e. the third row is
    // [0, 0, 1].
    *data *= sx;
    *(data + 3) *= sx;
    *(data + 1) *= sy;
    *(data + 4) *= sy;
    Py_RETURN_NONE;
}

static PyObject* mplutil_transform_translate(PyObject* self, PyObject* args)
{
    PyArrayObject* mtx;
    double tx, ty;
    if (!PyArg_ParseTuple(args, "O!dd", &PyArray_Type, &mtx, &tx, &ty)) {
        return NULL;
    }
    npy_intp* dims = PyArray_DIMS(mtx);
    if ((NPY_ARRAY_CARRAY & ~PyArray_FLAGS(mtx))
            || (PyArray_NDIM(mtx) != 2) || (dims[0] != 3) || (dims[1] != 3)
            || (PyArray_TYPE(mtx) != NPY_DOUBLE)) {
        PyErr_SetString(
                PyExc_ValueError,
                "Only C-contiguous 3x3 double arrays are supported");
        return NULL;
    }
    double* data = (double*)PyArray_DATA(mtx);
    // Assume that mtx is a valid transformation matrix; i.e. the third row is
    // [0, 0, 1].
    *(data + 2) += tx;
    *(data + 5) *= ty;
    Py_RETURN_NONE;
}

static PyMethodDef utilmethods[] = {
    {"transform_scale", mplutil_transform_scale, METH_VARARGS,
     "transform_scale(mtx, sx, sy)\n"
     "Helper for Affine2D.scale."},
    {"transform_translate", mplutil_transform_translate, METH_VARARGS,
     "transform_translate(mtx, tx, ty)\n"
     "Helper for Affine2D.translate."},
    {NULL, NULL, 0, NULL}
};

static PyModuleDef utilmodule = {
    PyModuleDef_HEAD_INIT,
    "_util",
    "Utilities for Matplotlib.",
    -1,
    utilmethods
};

PyMODINIT_FUNC
PyInit__util(void)
{
    PyObject* m;
    if (!(m = PyModule_Create(&utilmodule))) {
        return NULL;
    }
    import_array();
    return m;
}
