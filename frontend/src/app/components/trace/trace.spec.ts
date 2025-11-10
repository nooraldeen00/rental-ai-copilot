import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Trace } from './trace';

describe('Trace', () => {
  let component: Trace;
  let fixture: ComponentFixture<Trace>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Trace]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Trace);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
