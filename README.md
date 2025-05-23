Adobe Flash SWF file parser and AVM2 virtual machine implementation in pure Python.

This fork is hacky and I'll only update it when I need it.

## Assumptions

- I just needed to run a particular SWF and not to implement a full-featured virtual machine.
- I don't care a lot about performance, I rather care about maintainability.

## Recipes

### Parse an SWF file

```python
from pathlib import Path

from avm2.swf.parser import parse_swf

tags = list(parse_swf(Path('heroes.swf').read_bytes()))
```

### Execute a code tag

```python
from typing import Iterable

from avm2.swf.enums import TagType
from avm2.swf.types import Tag
from avm2.vm import execute_tag

tags: Iterable[Tag] = ...

for tag in tags:
    if tag.type_ == TagType.DO_ABC:
        machine = execute_tag(tag)
```

### Call a method

```python
from avm2.runtime import undefined
from avm2.vm import VirtualMachine

machine: VirtualMachine = ...

machine.call_method('battle.BattleCore.hitrateIntensity', undefined, 4, 8)
```

## Links

- https://burgerlib.readthedocs.io/en/latest/avm2overview.pdf
- https://open-flash.github.io/mirrors/swf-spec-19.pdf
- https://github.com/ruffle-rs/ruffle/tree/master/core/src/avm2
- https://github.com/ArachisH/Flazzy

### [`abcFormat.txt`](https://github.com/nxmirrors/tamarin-central/blob/master/core/abcFormat.txt)

```text
// ***** BEGIN LICENSE BLOCK *****
// Version: MPL 1.1/GPL 2.0/LGPL 2.1
//
// The contents of this file are subject to the Mozilla Public License Version
// 1.1 (the "License"); you may not use this file except in compliance with
// the License. You may obtain a copy of the License at
// http://www.mozilla.org/MPL/
//
// Software distributed under the License is distributed on an "AS IS" basis,
// WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
// for the specific language governing rights and limitations under the
// License.
//
// The Original Code is [Open Source Virtual Machine.].
//
// The Initial Developer of the Original Code is
// Adobe System Incorporated.
// Portions created by the Initial Developer are Copyright (C) 2005-2006
// the Initial Developer. All Rights Reserved.
//
// Contributor(s):
//   Adobe AS3 Team
//
// Alternatively, the contents of this file may be used under the terms of
// either the GNU General Public License Version 2 or later (the "GPL"), or
// the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
// in which case the provisions of the GPL or the LGPL are applicable instead
// of those above. If you wish to allow use of your version of this file only
// under the terms of either the GPL or the LGPL, and not to allow others to
// use your version of this file under the terms of the MPL, indicate your
// decision by deleting the provisions above and replace them with the notice
// and other provisions required by the GPL or the LGPL. If you do not delete
// the provisions above, a recipient may use your version of this file under
// the terms of any one of the MPL, the GPL or the LGPL.
//
// ***** END LICENSE BLOCK *****

This file stays synchronized with the source code.  To view
previous formats that we don't support, sync backwards in
perforce.


U30 - This is a 30 bit integer value encoded with a variable number of bytes to save space.
All U30's are encoded as 1-5 bytes depending on the value (larger values need more space).  
The encoding method is if the hi bit in the current byte is set, then the next byte is also
part of the value.  Each bit in a byte contributes 7 bits to the value, with the hi bit telling
us whether to use the next byte, or if this is the last byte for the value.  This enables us to 
use 30 bit numbers for everything, but still not take up enormous amounts of space.     

If more than 30 nonzero bits are present for a U30 field, a verify error will occur.

S32,U32 - same as U30 but 32 bits are allowed instead of being capped at 30.

The "0" entry of each constant pool is not used.  If the count for a given pool says there are
"n" entries in the pool, there are "n-1" entries in the file, corresponding to indices 1..(n-1).

AbcFile {
   U16 minor_version                  // = 16
   U16 major_version                  // = 46
   U30 constant_int_pool_count
   ConstantInteger[constant_int_pool_count] // Cpool entries for integers
   U30 constant_uint_pool_count
   ConstantUInteger[constant_uint_pool_count] // Cpool entries for uints
   U30 constant_double_pool_count
   ConstantDouble[constant_double_pool_count] // Cpool entries for doubles
   U30 constant_string_pool_count
   ConstantString[constant_string_pool_count] // Cpool entries for strings
   U30 constant_namespace_pool_count
   ConstantNamespace[constant_namespace_pool_count] // Cpool entries for namespaces
   U30 constant_namespace_set_pool_count
   ConstantNamespaceSet[constant_namespace_set_pool_count] //Cpool entries for namespace sets
   U30 constant_multiname_pool_count
   ConstantMultiname[constant_multiname_pool_count] //Cpool entries for Multinames, Qnames, RTQnames, and RTQnamesLate
   U30 methods_count
   MethodInfo[methods_count]
   U30 metadata_count
   MetadataInfo[metadata_count]
   U30 class_count
   InstanceInfo[class_count]
   ClassInfo[class_count]
   U30 script_count
   ScriptInfo[script_count]         // ScriptInfo[script_count-1] is main entry point
   U30 bodies_count
   MethodBody[bodies_count]
}


ConstantInteger {
   S32 value
}

ConstantUInteger {
   U32 value
}

ConstantDouble {
   U64 doublebits (little endian)
}

ConstantString {
   U30 length
   U8[length]  // UTF-8 encoded string
}

ConstantNamespace {
   U8 kind
   union {
      kind=8,5,22,23,24,25,26 { // CONSTANT_Namespace, CONSTANT_PrivateNamespace, CONSTANT_PackageNamespace, CONSTANT_PacakgeInternalNamespace, CONSTANT_ProtectedNamespace, CONSTANT_ExplicitNamespace, CONSTANT_StaticProtectedNamespace
         U30 name_index                    // CONSTANT_Utf8 uri (maybe 0)
      }
   }
}

ConstantNamespaceSet {
   U30 namespace_count  
   U30[namespace_count] // CONSTANT_Namespace
}

ConstantMultiname {
   U8 kind
   union {
      kind=7,13 { // CONSTANT_Qname + CONSTANT_QnameA
         U30 namespace_index			// CONSTANT_Namespace, 0=AnyNamespace wildcard
         U30 name_index					// CONSTANT_Utf8, 0=AnyName wildcard
      }
      kind=9,14 { // CONSTANT_Multiname, CONSTANT_MultinameA
         U30 name_index                    // CONSTANT_Utf8  simple name.  0=AnyName wildcard
         U30 namespace_set_index           
      }
      kind=15,16 { // CONSTANT_RTQname + CONSTANT_RTQnameA
         U30 name_index				// CONSTANT_utf8, 0=AnyName wildcard
      }
      kind=27 { // CONSTANT_MultinameL	
	 U30 namespace_set_index	
      kind=17,18 // CONSTANT_RTQnameL + CONSTANT_RTQnameLA
   }
}

Traits {
    U30 count              
    Trait[count] {
	    U30 name_index                     // CONSTANT_QName
        U8  kind                           // hi 4 bits are flags, 0x04: (1=has_metadata, 0=no metadata)
        union {
           kind=0,6 { // slot, const
              U30 slot_id                  // 0=autoassign
              U30 type_index               // CONSTANT_Multiname, 0=Object
              U30 value_index              // CONSTANT_<kind> or 0 for undefined - <kind> depends on the value of value_kind
              U8  value_kind               // cpool kind the value is, only present if value_index != 0
           }
           kind=1,2,3 { // method, getter, setter
              U30 disp_id			  // 0=autoassign
              U30 method_info         // method must be parsed already
   		     // attrs are stored in the hi 4 bits of the kind byte
             // 0x01: (1=final,0=virtual), 0x02: (1=override,0=new)
           }
           kind=4 { // class
              U30 slot_id                  // 0=autoassign
              U30 class_info               // class must have been parsed already
           }
           kind=5 { // function
              U30 slot_index          // 0=autoassign
              U30 method_info		  // method_info of function residing in this slot
           }
        }
        if ( (kind >> 4) & 0x04 )  // these are only present when the kind contains the has_metadata flag
        {
            U30 metadata_count           // Number of metadata
            U30 metadata[count]          // MetadataInfo indices
        }
    }
}

MetadataInfo {
    U30 name_index                         // CONSTANT_utf8
    U30 values_count                       // # of values in this metadata
    U30 keys[values_count]                 // CONSTANT_utf8, 0 = keyless
    U30 values[values_count]               // CONSTANT_utf8 
}

InstanceInfo {
    U30 name_index                    // CONSTANT_QName (definition)
    U30 super_index                   // CONSTANT_Multiname (reference)
    U8  flags                         // 1 = sealed, 0 = dynamic
				      // 2 = final
				      // 4 = interface
    U30 protectedNS                   if flags & 8
    U30 interfaces_count
    U30 interfaces[interfaces_count]  // CONSTANT_Multiname (references)
    U30 iinit_index                   // MethodInfo
    Traits instance_traits
}

ClassInfo {
    U30 cinit_index                     // MethodInfo
    Traits static_traits
}

ScriptInfo {
    U30 init_index                      // MethodInfo
    Traits traits
}

// A MethodInfo describes the method signature
MethodInfo {
    U30 param_count
    U30 ret_type					  // CONSTANT_Multiname, 0=any type (*)
    U30 param_types[param_count]	  // CONSTANT_Multiname, 0=any type (*)
    U30 name_index                    // 0=no name.
    // 1=need_arguments, 2=need_activation, 4=need_rest 8=has_optional 16=ignore_rest, 32=explicit, 64=setsdxns, 128=has_paramnames
    U8 flags                          
    U30 optional_count                // if has_optional
    ValueKind[optional_count]         // if has_optional
    U30 param_names[param_count]      // if has_paramnames
}

ValueKind {
    U30 value_index   // the index for the value in the cpool
    U8 value_kind     // the kind indicating which cpool the value is in
}

// A MethodBody describes the method implementation.  
// not required for native methods or interface methods.
MethodBody {
	U30 method_info
    U30 max_stack
    U30 max_regs
    U30 scope_depth
    U30 max_scope
    U30 code_length
    U8 code[code_length]
    U30 ex_count
    Exception[ex_count]
    Traits traits	// activation traits
}

Exception {
    U30 start                           // Offsets of beginning and
    U30 end                             // end of the try block
    U30 target                          // Target PC to transfer control to (catch)
    U30 type_index                      // Type matched by this exception handler
    U30 name_index                      // Name of the exception variable
}
```
