package main

import (
	"fmt"
	"bufio"
	"strings"
	"strconv"
	"os"
	"time"
	"unicode"
	"flag"
)

type pulse struct {
	val int
	resp chan int
}

type pulsefn func(pulse)

var initbut, cycbut chan int
var initbutdone chan int
var teststart chan int
var testdone chan int
var ppunch chan string
var mpsw, conssw, cycsw, multsw, divsw, prsw chan [2]string
var accsw [20]chan [2]string
var ftsw [3]chan [2]string
var width, height int
var cardscanner *bufio.Scanner
var punchwriter *bufio.Writer
var demomode, tkkludge, usecontrol *bool
var testcycles *int

func b2is(b bool) string {
	if b {
		return "1"
	}
	return "0"
}

func fanout(in chan pulse, out []chan pulse) {
	var q pulse

	q.resp = make(chan int)
	for {
		p :=<- in
		nresp := 0
		if p.val != 0 {
			q.val = p.val
			for _,c := range out {
foo:
				for {
					select {
					case c <- q:
						break foo
					case <- q.resp:
						nresp++
					}
				}
			}
		}
		for nresp < len(out) {
			<- q.resp
			nresp++
		}
		p.resp <- 1
	}
}

func tee(a, b chan pulse) chan pulse {
	var t = make(chan pulse)
	go func() {
		for {
			select {
			case pa := <-a:
				if pa.val != 0 {
					t <- pa
				}
			case pb := <-b:
				if pb.val != 0 {
					t <- pb
				}
			case pt := <-t:
				if pt.val != 0 {
					var pt2 pulse
					if a != nil {
						pt2.resp = make(chan int)
						pt2.val = pt.val
						a <- pt2
						<- pt2.resp
					}
					if b != nil {
						pt2.resp = make(chan int)
						pt2.val = pt.val
						b <- pt2
						<- pt2.resp
					}
					pt.resp <- 1
				}
			}
		}
	}()
	return t
}

func dumpall() {
	fmt.Println()
	fmt.Println(initstat())
	fmt.Println(mpstat())
	acchdr := "      9876543210 9876543210 r 123456789012"
	fmt.Printf("%s   %s\n", acchdr, acchdr)
	for i := 0; i < 20; i += 2 {
		fmt.Print(accstat(i))
		fmt.Print("   ")
		fmt.Println(accstat(i+1))
	}
	fmt.Println(divsrstat2())
	fmt.Println(multstat())
	for i := 0; i < 3; i++ {
		fmt.Println(ftstat(i))
	}
	fmt.Println(consstat())
	fmt.Println()
}

func proccmd(cmd string) int {
	f := strings.Fields(cmd)
	for i, s := range f {
		if s[0] == '#' {
			f = f[:i]
			break
		}
	}
	if len(f) == 0 {
		return 0
	}
	switch f[0] {
	case "b":
		if len(f) != 2 {
			fmt.Println("button syntax: b button")
			break
		}
		switch f[1] {
		case "c":
			initbut <- 5
			<- initbutdone
		case "i":
			initbut <- 4
			<- initbutdone
		case "p":
			cycbut <- 1
			<- cycbutdone
		case "r":
			initbut <- 3
			<- initbutdone
		}
	case "n":
		cycbut <- 1
		<- cycbutdone
		dumpall()
	case "d":
		if len(f) != 2 {
			fmt.Println("Status syntax: d unit")
			break
		}
		switch f[1][0] {
		case 'a':
			unit, _ := strconv.Atoi(f[1][1:])
			fmt.Println(accstat(unit-1))
		case 'b':
			fmt.Println(debugstat())
		case 'c':
			fmt.Println(consstat())
		case 'd':
			fmt.Println(divsrstat2())
		case 'f':
			unit, _ := strconv.Atoi(f[1][1:])
			fmt.Println(ftstat(unit-1))
		case 'i':
			fmt.Println(initstat())
		case 'm':
			fmt.Println(multstat())
		case 'p':
			fmt.Println(mpstat())
		}
	case "D":
		dumpall()
	case "f":
		if len(f) != 3 {
			fmt.Println("file syntax: f (r|p) filename")
			break
		}
		switch f[1] {
		case "r":
			fp, err := os.Open(f[2])
			if err != nil {
				fmt.Printf("Card reader open: %s\n", err)
				break
			}
			cardscanner = bufio.NewScanner(fp)
		case "p":
			fp, err := os.Create(f[2])
			if err != nil {
				fmt.Printf("Card punch open: %s\n", err)
				break
			}
			punchwriter = bufio.NewWriter(fp)
		}
	case "l":
		if len(f) != 2 {
			fmt.Println("Load syntax: l file")
			break
		}
		fd, err := os.Open(f[1])
		if err != nil {
			fd, err = os.Open("programs/" + f[1])
			if err != nil {
				fmt.Println(err)
				break
			}
		}
		sc := bufio.NewScanner(fd)
		for sc.Scan() {
			if proccmd(sc.Text()) < 0 {
				break
			}
		}
		fd.Close()
	case "p":
		if len(f) != 3 {
			fmt.Println("Invalid jumper spec", cmd)
			break
		}
		p1 := strings.Split(f[1], ".")
		p2 := strings.Split(f[2], ".")
		/*
		 * Ugly special case of 20 digit interconnects
		 */
		if len(p1) == 2 && p1[0][0] == 'a' && len(p1[1]) >= 2 &&
				(p1[1][:2] == "st" || p1[1][:2] == "su" ||
				 p1[1][:2] == "il" || p1[1][:2] == "ir") {
			accinterconnect(p1, p2)
			break
		}
		ch := make(chan pulse)
		switch {
		case p1[0] == "ad":
			if len(p1) != 4 {
				fmt.Println("Adapter jumper syntax: ad.ilk.unit.param")
				break;
			}
			unit, _ := strconv.Atoi(p1[2])
			param, _ := strconv.Atoi(p1[3])
			adplug(p1[1], 1, unit - 1, param, ch)
		case p1[0][0] == 'a':
			if len(p1) != 2 {
				fmt.Println("Accumulator jumper syntax: aunit.terminal")
				break
			}
			unit, _ := strconv.Atoi(p1[0][1:])
			accplug(unit - 1, p1[1], ch)
		case p1[0] == "c":
			if len(p1) != 2 {
				fmt.Println("Invalid constant jumper:", cmd)
				break
			}
			consplug(p1[1], ch)
		case p1[0] == "d":
			if len(p1) != 2 {
				fmt.Println("Divider jumper syntax: d.terminal")
				break
			}
			divsrplug(p1[1], ch)
		case p1[0][0] == 'f':
			if len(p1) != 2 {
				fmt.Println("Function table jumper syntax: funit.terminal")
				break
			}
			unit, _ := strconv.Atoi(p1[0][1:])
			ftplug(unit - 1, p1[1], ch)
		case p1[0] == "i":
			if len(p1) != 2 {
				fmt.Println("Initiator jumper syntax: i.terminal")
				break
			}
			initplug(p1[1], ch)
		case p1[0] == "m":
			if len(p1) != 2 {
				fmt.Println("Multiplier jumper syntax: m.terminal")
				break
			}
			multplug(p1[1], ch)
		case p1[0] == "p":
			mpplug(p1[1], ch)
		case unicode.IsDigit(rune(p1[0][0])):
			hpos := strings.IndexByte(p1[0], '-')
			if hpos == -1 {
				tray, _ := strconv.Atoi(p1[0])
				if tray < 1 {
					fmt.Println("Invalid data trunk", p1[0])
					break
				}
				trunkrecv(0, tray - 1, ch)
			} else {
				tray, _ := strconv.Atoi(p1[0][:hpos])
				line, _ := strconv.Atoi(p1[0][hpos+1:])
				trunkrecv(1, (tray - 1) * 11 + line - 1, ch)
			}
		default:
			fmt.Println("Invalid jack spec: ", p1)
		}
		switch {
		case p2[0] == "ad":
			if len(p2) != 4 {
				fmt.Println("Adapter jumper syntax: ad.ilk.unit.param")
				break;
			}
			unit, _ := strconv.Atoi(p2[2])
			param, _ := strconv.Atoi(p2[3])
			adplug(p2[1], 0, unit - 1, param, ch)
		case p2[0][0] == 'a':
			if len(p2) != 2 {
				fmt.Println("Accumulator jumper syntax: aunit.terminal")
				break
			}
			unit, _ := strconv.Atoi(p2[0][1:])
			accplug(unit - 1, p2[1], ch)
		case p2[0] == "debug":
			if len(p2) != 2 {
				fmt.Println("Debugger jumper syntax: debug.bpn")
				break
			}
			unit, _ := strconv.Atoi(p2[1][2:])
			debugplug(unit, ch, f[1])
		case p2[0] == "c":
			if len(p2) != 2 {
				fmt.Println("Invalid constant jumper:", cmd)
				break
			}
			consplug(p2[1], ch)
		case p2[0] == "d":
			if len(p2) != 2 {
				fmt.Println("Divider jumper syntax: d.terminal")
				break
			}
			divsrplug(p2[1], ch)
		case p2[0][0] == 'f':
			if len(p2) != 2 {
				fmt.Println("Function table jumper syntax: funit.terminal")
				break
			}
			unit, _ := strconv.Atoi(p2[0][1:])
			ftplug(unit - 1, p2[1], ch)
		case p2[0] == "i":
			if len(p2) != 2 {
				fmt.Println("Initiator jumper syntax: i.terminal")
				break
			}
			initplug(p2[1], ch)
		case p2[0] == "m":
			if len(p2) != 2 {
				fmt.Println("Multiplier jumper syntax: m.terminal")
				break
			}
			multplug(p2[1], ch)
		case p2[0] == "p":
			mpplug(p2[1], ch)
		case unicode.IsDigit(rune(p2[0][0])):
			hpos := strings.IndexByte(p2[0], '-')
			if hpos == -1 {
				tray, _ := strconv.Atoi(p2[0])
				if tray < 1 {
					fmt.Println("Invalid data trunk", p2[0])
					break
				}
				trunkxmit(0, tray - 1, ch)
			} else {
				tray, _ := strconv.Atoi(p2[0][:hpos])
				line, _ := strconv.Atoi(p2[0][hpos+1:])
				trunkxmit(1, (tray - 1) * 11 + line - 1, ch)
			}
		default:
			fmt.Println("Invalid jack spec: ", p2)
		}
	case "q":
		return -1
	case "r":
		if len(f) != 2 {
			fmt.Println("Status syntax: r unit")
			break
		}
		p := strings.Split(f[1], ".")
		switch p[0] {
		case "a":
			if len(p) != 2 {
				fmt.Println("Accumulator reset syntax: r a.unit")
			} else {
				unit, _ := strconv.Atoi(p[1])
				accreset(unit)
			}
		case "b":
			debugreset()
		case "c":
			consreset()
		case "d":
			divreset()
		case "f":
			if len(p) != 2 {
				fmt.Println("Function table reset syntax: r f.unit")
			} else {
				unit, _ := strconv.Atoi(p[1])
				ftreset(unit)
			}
		case "i":
			initreset()
		case "m":
			multreset()
		case "p":
			mpreset()
		}
	case "R":
		initreset()
		cycreset()
		debugreset()
		mpreset()
		ftreset(0)
		ftreset(1)
		ftreset(2)
		for i := 0; i < 20; i++ {
			accreset(i)
		}
		divreset()
		multreset()
		consreset()
		prreset()
		adreset()
		trayreset()
	case "s":
		if len(f) < 3 {
			fmt.Println("No switch setting")
			break
		}
		p := strings.Split(f[1], ".")
		switch {
		case p[0][0] == 'a':
			if len(p) != 2 {
				fmt.Println("Invalid accumulator switch:", cmd)
			} else {
				unit, _ := strconv.Atoi(p[0][1:])
				accsw[unit-1] <- [2]string{p[1], f[2]}
			}
		case p[0] == "c":
			if len(p) != 2 {
				fmt.Println("Constant switch syntax: s c.switch value")
			} else {
				conssw <- [2]string{p[1], f[2]}
			}
		case p[0] == "cy":
			if len(p) != 2 {
				fmt.Println("Cycling switch syntax: s cy.switch value")
			} else {
				cycsw <- [2]string{p[1], f[2]}
			}
		case p[0] == "d" || p[0] == "ds":
			if len(p) != 2 {
				fmt.Println("Divider switch syntax: s d.switch value")
			} else {
				divsw <- [2]string{p[1], f[2]}
			}
		case p[0][0] == 'f':
			if len(p) != 2 {
				fmt.Println("Function table switch syntax: s funit.switch value", cmd)
			} else {
				unit, _ := strconv.Atoi(p[0][1:])
				ftsw[unit-1] <- [2]string{p[1], f[2]}
			}
		case p[0] == "m":
			if len(p) != 2 {
				fmt.Println("Multiplier switch syntax: s m.switch value")
			} else {
				multsw <- [2]string{p[1], f[2]}
			}
		case p[0] == "p":
			if len(p) != 2 {
				fmt.Println("Programmer switch syntax: s p.switch value")
			} else {
				mpsw <- [2]string{p[1], f[2]}
			}
		case p[0] == "pr":
			if len(p) != 2 {
				fmt.Println("Printer switch syntax: s pr.switch value")
			} else {
				prsw <- [2]string{p[1], f[2]}
			}
		default:
			fmt.Printf("unknown unit for switch: %s\n", p[0])
		}
	case "set":
		if len(f) != 3 {
			fmt.Println("set syntax: set a13 -9876543210")
			break
		}
		unit, _ := strconv.Atoi(f[1][1:])
		value, _ := strconv.ParseInt(f[2], 10, 64)
		accset(unit - 1, value)
	case "u":
	case "dt":
	case "pt":
	default:
		fmt.Printf("Unknown command: %s\n", cmd)
	}
	return 0
}

//
//  This code assumes that we're running on a Raspberry Pi
// with Linux.  We also assume that the necessary exports
// have already been done.
//
func ctlstation() {
	fd5, err := os.Open("/sys/class/gpio/gpio5/value")
	if err != nil {
		return
	}
	fd6, _ := os.Open("/sys/class/gpio/gpio6/value")
	fd13, _ := os.Open("/sys/class/gpio/gpio13/value")
	fd19, _ := os.Open("/sys/class/gpio/gpio19/value")
	fd26, _ := os.Open("/sys/class/gpio/gpio26/value")
	fd21, _ := os.Open("/sys/class/gpio/gpio21/value")
	fd20, _ := os.Open("/sys/class/gpio/gpio20/value")

	buf := make([]byte, 1)

	curstate := 0
	filterset := 0
	filtercnt := 0
	// Seriously ugly hack to give other goprocs time to get initialized
	time.Sleep(100*time.Millisecond)
	for {
		time.Sleep(10*time.Millisecond)
		newstate := 0
		n, err := fd5.ReadAt(buf, 0)
		if n != 1 {
			fmt.Println(err)
		}
		if buf[0] == '0' {
			newstate |= 0x02
		}
		fd6.ReadAt(buf, 0)
		if buf[0] == '0' {
			newstate |= 0x01
		}
		fd13.ReadAt(buf, 0)
		if buf[0] == '0' {
			newstate |= 0x40
		}
		fd19.ReadAt(buf, 0)
		if buf[0] == '0' {
			newstate |= 0x20
		}
		fd26.ReadAt(buf, 0)
		if buf[0] == '0' {
			newstate |= 0x10
		}
		fd21.ReadAt(buf, 0)
		if buf[0] == '0' {
			newstate |= 0x04
		}
		fd20.ReadAt(buf, 0)
		if buf[0] == '0' {
			newstate |= 0x08
		}
		if newstate != filterset || newstate & 0x70 == 0 {
			filtercnt = 0
			filterset = newstate
		} else {
			filtercnt++
		}
		if filtercnt == 4 {
			if newstate != curstate {
				diff := newstate ^ curstate
				if diff & 0x70 != 0 {
					switch newstate & 0x70 {
					case 0x10:
						proccmd("s cy.op 1a")
					case 0x20:
						proccmd("s cy.op 1p")
					case 0x60:
						proccmd("s cy.op co")
					}
				}
				if diff & 0x01 != 0 && newstate & 0x01 != 0 {
					proccmd("b c")
				}
				if diff & 0x02 != 0 && newstate & 0x02 != 0 {
					proccmd("b r")
				}
				if diff & 0x04 != 0 && newstate & 0x04 != 0 {
					proccmd("b i")
				}
				if diff & 0x08 != 0 && newstate & 0x08 != 0 {
					proccmd("b p")
				}
				curstate = newstate
			}
		}
	}
}

func main() {
	var ftcyc [3]chan pulse

	flag.Usage = func () {
		fmt.Fprintf(os.Stderr, "Usage: %s [options] [configuration file]\n", os.Args[0])
		flag.PrintDefaults()
	}
	usecontrol = flag.Bool("c", false, "use a portable control station connected to GPIO pins")
	demomode = flag.Bool("D", false, "automatically cycle among perspectives")
	nogui := flag.Bool("g", false, "run without GUI")
	tkkludge = flag.Bool("K", false, "work around wish memory leaks")
	wp := flag.Int("w", 0, "`width` of the simulation window in pixels")
	testcycles = flag.Int("t", 0, "run for n add cycles and dump state")
	flag.Parse()
	width = *wp
	if !*nogui {
		go gui()
		ppunch = make(chan string)
	}
	if *usecontrol {
		go ctlstation()
	}

	initbut = make(chan int)
	initbutdone = make(chan int)
	cycsw = make(chan [2]string)
	cycbut = make(chan int)
	cycbutdone = make(chan int)
	teststart = make(chan int)
	testdone = make(chan int)
	mpsw = make(chan [2]string)
	divsw = make(chan [2]string)
	multsw = make(chan [2]string)
	conssw = make(chan [2]string)
	cycout := make(chan pulse)
	cyctrunk := make([]chan pulse, 0, 40)
	var f []pulsefn
	f = append(f, makeinitiatepulse())
  f = append(f, makemppulse())
  f = append(f, makedivpulse())
	multcyc := make(chan pulse)
	conscyc := make(chan pulse)
	prsw = make(chan [2]string)
	p := append(cyctrunk, multcyc, conscyc)
	for i := 0; i < 20; i++ {
		accsw[i] = make(chan [2]string)
		f = append(f, makeaccpulse(i))
	}
	for i := 0; i < 3; i++ {
		ftsw[i] = make(chan [2]string)
		ftcyc[i] = make(chan pulse)
		p = append(p, ftcyc[i])
	}
	go fanout(cycout, p)

	go consctl(conssw)
	go mpctl(mpsw)
	go cyclectl(cycsw)
	go divsrctl(divsw)
	go multctl(multsw)
	go prctl(prsw)

	go initiateunit(initbut, initbutdone)
	go mpunit()
	go cycleunit(cycout, f, cycbut)
	go divunit()
	go multunit(multcyc)
	go consunit(conscyc)
	for i := 0; i < 20; i++ {
		go accctl(i, accsw[i])
		go accunit(i)
	}
	for i := 0; i < 3; i++ {
		go ftctl(i, ftsw[i])
		go ftunit(i, ftcyc[i])
	}

	if flag.NArg() >= 1 {
		// Seriously ugly hack to give other goprocs time to get initialized
		time.Sleep(100*time.Millisecond)
		proccmd("l " + flag.Arg(0))
	}

	if *testcycles > 0 {
		teststart <- 1
		<- testdone
		dumpall()
		return
	}

	sc := bufio.NewScanner(os.Stdin)
	var prompt = func() {
		acycmu.Lock()
		fmt.Printf("%04d> ", acyc % 10000)
		acycmu.Unlock()
	}
	prompt()
	for sc.Scan() {
		if proccmd(sc.Text()) < 0 {
			break
		}
		prompt()
	}
}
