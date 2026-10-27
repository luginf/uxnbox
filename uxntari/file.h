/* Peripherique fichier de varvara (deux canaux, A en $a0 et B en $b0). */
#ifndef FILE_H
#define FILE_H

void file_reset(int id);
int file_init(int id, int addr);
int file_read(int id, int addr, int len);
int file_write(int id, int addr, int len, int flags);
int file_stat(int id, int addr, int len);
int file_delete(int id);

#endif
