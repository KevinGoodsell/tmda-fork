#include <Python.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/wait.h>

#define STDIO  1
#define STDERR 2
#define CP_OUT 3

int Send(int Pipe, char *String)
{
  int i, j;
  
  i = 0;
  while (i < (strlen(String) + 1))
  {
    j = write(Pipe, String + i, strlen(String) + 1 - i);
    if (j == -1) return -1;
    i += j;
  }
  return 0;
}

static PyObject *CheckPassword(PyObject *self, PyObject *args)
{
  int ChildPID, WStat, Temp, Pipes[2];
  char *User, *Password, *BinCheckPassword, *BinTrue;

  /* Get arguments */
  if (!PyArg_ParseTuple(args, "ssss", &User, &Password, &BinCheckPassword,
    &BinTrue))
    return NULL;  

  /* Create a pipe to CP_OUT */
  close(CP_OUT);
  if (pipe(Pipes) == -1)
  {
    PyErr_SetString(PyExc_OSError, "Could not create pipe.");
    return NULL;
  }
  if (Pipes[0] != CP_OUT)
  {
    PyErr_SetString(PyExc_OSError, "Pipe assignment error.");
    return NULL;
  }
  
  /* Fork into two processes, one that pipes in the user name and password,
     and one that launches the checkpassword program */
  switch (ChildPID = fork())
  {
    case -1:  /* failed fork */
    {
      PyErr_SetString(PyExc_OSError, "Unable to fork.");
      return NULL;
    }
    case 0:   /* launch checkpassword in child */
      close(Pipes[1]); /* child uses reader only */
      execl(BinCheckPassword, Password, BinTrue);
      {
        PyErr_SetString(PyExc_OSError, "Could not run checkpassword.");
        return NULL;
      }
  }
  
  close(Pipes[0]); /* parent uses writer only */
  
  /* Send user name & password */
  if (Send(Pipes[1], User))
  {
    PyErr_SetString(PyExc_OSError, "Could send user name.");
    return NULL;
  }
  if (Send(Pipes[1], Password))
  {
    PyErr_SetString(PyExc_OSError, "Could not send password.");
    return NULL;
  }
  
  /* Close the pipe */
  close(Pipes[1]);
  
  do
    Temp = waitpid(ChildPID, &WStat, 0);
  while ((Temp == -1) && (errno == EINTR));
  if (Temp == -1) return Py_BuildValue("i", 2);
  if (WStat & 127)
  {
    PyErr_SetString(PyExc_OSError, "checkpassword thread crashed.");
    return NULL;
  }
  if (WStat >> 8) return Py_BuildValue("i", 0);
  return Py_BuildValue("i", 1);
}

static PyMethodDef CheckPasswordMethods[] =
{
  {"CheckPassword",  CheckPassword, METH_VARARGS, "Check a password."},
  {NULL, NULL, 0, NULL}        /* Sentinel */
};

void initCheckPassword(void)
{
  (void) Py_InitModule("CheckPassword", CheckPasswordMethods);
}

