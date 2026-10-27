#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include "uxn.h"
#include "file.h"

enum { IDLE, FILE_READ, FILE_WRITE, DIR_READ, DIR_WRITE };

typedef struct {
	FILE *f;
	DIR *dir;
	char path[256];
	int named, state;
} UxnFile;

static UxnFile ufs[2];

static int
is_dir_path(const char *p)
{
	int n = (int)strlen(p);
	return n > 0 && (p[n - 1] == '/' || p[n - 1] == '\\');
}

static int
is_dir_real(const char *p)
{
	struct stat st;
	return stat(p, &st) == 0 && S_ISDIR(st.st_mode);
}

void
file_reset(int id)
{
	UxnFile *u = &ufs[id];
	if(u->state == FILE_READ || u->state == FILE_WRITE) fclose(u->f);
	else if(u->state == DIR_READ) closedir(u->dir);
	u->state = IDLE;
}

static int
file_open(int id, int want_write, int flags)
{
	UxnFile *u = &ufs[id];
	if(want_write) {
		if(u->state == FILE_WRITE || u->state == DIR_WRITE) return 1;
		file_reset(id);
		if(is_dir_path(u->path)) {
			char tmp[256];
			strcpy(tmp, u->path);
			tmp[strlen(tmp) - 1] = 0;
			if(!is_dir_real(tmp)) mkdir(tmp, 0755);
			u->state = is_dir_real(tmp) ? DIR_WRITE : IDLE;
		} else if((u->f = fopen(u->path, (flags & 1) ? "ab" : "wb")))
			u->state = FILE_WRITE;
	} else {
		if(u->state == FILE_READ || u->state == DIR_READ) return 1;
		file_reset(id);
		if(is_dir_real(u->path)) {
			if((u->dir = opendir(u->path))) u->state = DIR_READ;
		} else if((u->f = fopen(u->path, "rb")))
			u->state = FILE_READ;
	}
	return u->state != IDLE;
}

int
file_init(int id, int addr)
{
	UxnFile *u = &ufs[id];
	int n = 0;
	file_reset(id);
	while(ram[(addr + n) & 0xffff] && n < 255) {
		u->path[n] = ram[(addr + n) & 0xffff];
		n++;
	}
	u->path[n] = 0;
	u->named = 1;
	return 0;
}

static int
clamp(int addr, int len)
{
	return addr + len > 0x10000 ? 0x10000 - addr : len;
}

/* Liste le repertoire : taille sur 4 chiffres hexa (---- pour un repertoire),
   tabulation, nom, saut de ligne. Une entree tronquee par len est perdue. */
static int
read_dir(UxnFile *u, int addr, int len)
{
	int n = 0, k;
	struct dirent *de;
	char full[512], line[300];
	struct stat st;
	while(n < len - 1 && (de = readdir(u->dir))) {
		const char *name = de->d_name;
		int dir, err, sl = (int)strlen(u->path);
		if(name[0] == '.' && (!name[1] || (name[1] == '.' && !name[2]))) continue;
		sprintf(full, "%s%s%s", u->path, (sl && u->path[sl - 1] != '/' && u->path[sl - 1] != '\\') ? "/" : "", name);
		err = stat(full, &st);
		dir = !err && S_ISDIR(st.st_mode);
		if(dir) strcpy(line, "----");
		else if(err) strcpy(line, "!!!!");
		else if((unsigned long)st.st_size >= 0x10000) strcpy(line, "????");
		else sprintf(line, "%04x", (unsigned)st.st_size);
		sprintf(line + 4, "\t%s%s\n", name, dir ? "/" : "");
		for(k = 0; line[k] && n < len; k++)
			ram[addr + n++] = (u8)line[k];
	}
	if(addr + n < 0x10000) ram[addr + n] = 0;
	return n;
}

int
file_read(int id, int addr, int len)
{
	UxnFile *u = &ufs[id];
	int n;
	if(!u->named) return 0;
	len = clamp(addr, len);
	if(!file_open(id, 0, 0)) return 0;
	if(u->state == FILE_READ) n = (int)fread(&ram[addr], 1, len, u->f);
	else n = read_dir(u, addr, len);
	if(len > 0 && n == 0) file_reset(id);
	return n;
}

int
file_write(int id, int addr, int len, int flags)
{
	UxnFile *u = &ufs[id];
	int n;
	if(!u->named) return 0;
	len = clamp(addr, len);
	if(!file_open(id, 1, flags)) return 0;
	if(u->state == FILE_WRITE) {
		n = (int)fwrite(&ram[addr], 1, len, u->f);
		return (n > 0 && fflush(u->f) != 0) ? 0 : n;
	}
	return 1;
}

/* Ecrit la taille sur len chiffres hexa, '!' en cas d'erreur, '-' pour un repertoire, '?' si trop grande */
int
file_stat(int id, int addr, int len)
{
	UxnFile *u = &ufs[id];
	struct stat st;
	int i, err, dir;
	if(!u->named) return 0;
	len = clamp(addr, len);
	err = stat(u->path, &st);
	dir = !err && S_ISDIR(st.st_mode);
	for(i = 0; i < len; i++) {
		int k = len - 1 - i;
		unsigned long size = (unsigned long)st.st_size;
		if(dir) ram[addr + i] = '-';
		else if(err) ram[addr + i] = '!';
		else if(len < 8 && size >> (4 * len)) ram[addr + i] = '?';
		else ram[addr + i] = "0123456789abcdef"[k >= 8 ? 0 : (size >> (4 * k)) & 0xf];
	}
	return len;
}

int
file_delete(int id)
{
	UxnFile *u = &ufs[id];
	if(!u->named) return 0;
	file_reset(id);
	return unlink(u->path) == 0;
}
