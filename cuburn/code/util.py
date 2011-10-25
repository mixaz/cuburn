"""
Provides tools and miscellaneous functions for building device code.
"""

import numpy as np
import tempita

def crep(s):
    """Escape for PTX assembly"""
    return '"%s"' % s.encode("string_escape")

class Template(tempita.Template):
    default_namespace = tempita.Template.default_namespace.copy()
Template.default_namespace.update({'np': np, 'crep': crep})

class HunkOCode(object):
    """An apparently passive container for device code."""
    # Use property objects to make these dynamic
    headers = ''
    decls = ''
    defs = ''

def assemble_code(*sections):
    return ''.join([''.join([getattr(sect, kind) for sect in sections])
                    for kind in ['headers', 'decls', 'defs']])

def apply_affine(x, y, xo, yo, packer):
    return Template("""
    {{xo}} = {{packer.xx}} * {{x}} + {{packer.xy}} * {{y}} + {{packer.xo}};
    {{yo}} = {{packer.yx}} * {{x}} + {{packer.yy}} * {{y}} + {{packer.yo}};
    """).substitute(locals())

class BaseCode(HunkOCode):
    headers = """
#include<cuda.h>
#include<stdint.h>
#include<stdio.h>
"""

    defs = r"""
#undef M_E
#undef M_LOG2E
#undef M_LOG10E
#undef M_LN2
#undef M_LN10
#undef M_PI
#undef M_PI_2
#undef M_PI_4
#undef M_1_PI
#undef M_2_PI
#undef M_2_SQRTPI
#undef M_SQRT2
#undef M_SQRT1_2

#define  M_E          2.71828174591064f
#define  M_LOG2E      1.44269502162933f
#define  M_LOG10E     0.43429449200630f
#define  M_LN2        0.69314718246460f
#define  M_LN10       2.30258512496948f
#define  M_PI         3.14159274101257f
#define  M_PI_2       1.57079637050629f
#define  M_PI_4       0.78539818525314f
#define  M_1_PI       0.31830987334251f
#define  M_2_PI       0.63661974668503f
#define  M_2_SQRTPI   1.12837922573090f
#define  M_SQRT2      1.41421353816986f
#define  M_SQRT1_2    0.70710676908493f

// TODO: use launch parameter preconfig to eliminate unnecessary parts
__device__
uint32_t gtid() {
    return threadIdx.x + blockDim.x *
            (threadIdx.y + blockDim.y *
                (threadIdx.z + blockDim.z *
                    (blockIdx.x + (gridDim.x * blockIdx.y))));
}

__device__
uint32_t trunca(float f) {
    // truncate as used in address calculations. note the use of a signed
    // conversion is intentional here (simplifies image bounds checking).
    uint32_t ret;
    asm("cvt.rni.s32.f32    %0,     %1;" : "=r"(ret) : "f"(f));
    return ret;
}

__global__
void zero_dptr(float* dptr, int size) {
    int i = (gridDim.x * blockIdx.y + blockIdx.x) * blockDim.x + threadIdx.x;
    if (i < size) {
        dptr[i] = 0.0f;
    }
}

/* read_half and write_half decode and encode, respectively, two
 * floating-point values from a 32-bit value (typed as a 'float' for
 * convenience but not really). The values are packed into u16s as a
 * proportion of a third value, as in 'ux = u16( x / d * (2^16-1) )'.
 * This is used during accumulation.
 *
 * TODO: also write a function that will efficiently add a value to the packed
 * values while incrementing the density, to improve the speed of this
 * approach when the alpha channel is present.
 */

__device__
void read_half(float &x, float &y, float xy, float den) {
    asm("\n\t{"
        "\n\t   .reg .u16       x, y;"
        "\n\t   .reg .f32       rc;"
        "\n\t   mov.b32         {x, y},     %2;"
        "\n\t   mul.f32         rc,         %3,     0f37800080;" // 1/65535.
        "\n\t   cvt.rn.f32.u16     %0,         x;"
        "\n\t   cvt.rn.f32.u16     %1,         y;"
        "\n\t   mul.f32         %0,         %0,     rc;"
        "\n\t   mul.f32         %1,         %1,     rc;"
        "\n\t}"
        : "=f"(x), "=f"(y) : "f"(xy), "f"(den));
}

__device__
void write_half(float &xy, float x, float y, float den) {
    asm("\n\t{"
        "\n\t   .reg .u16       x, y;"
        "\n\t   .reg .f32       rc, xf, yf;"
        "\n\t   rcp.approx.f32  rc,         %3;"
        "\n\t   mul.f32         rc,         rc,     65535.0;"
        "\n\t   mul.f32         xf,         %1,     rc;"
        "\n\t   mul.f32         yf,         %2,     rc;"
        "\n\t   cvt.rni.u16.f32 x,  xf;"
        "\n\t   cvt.rni.u16.f32 y,  yf;"
        "\n\t   mov.b32         %0,         {x, y};"
        "\n\t}"
        : "=f"(xy) : "f"(x), "f"(y), "f"(den));
}


"""

    @staticmethod
    def zero_dptr(mod, dptr, size, stream=None):
        """
        A memory zeroer which can be embedded in a stream. Size is the
        number of 4-byte words in the pointer.
        """
        zero = mod.get_function("zero_dptr")
        blocks = int(np.ceil(np.sqrt(size / 1024 + 1)))
        zero(dptr, np.int32(size), stream=stream,
             block=(1024, 1, 1), grid=(blocks, blocks, 1))


